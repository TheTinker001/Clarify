{
  description = "Clarify (Django) - development flake with run/test/seed entrypoints";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-darwin" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python312;

        # A tiny in-flake shim for the (very small) `with_asserts` dependency
        # used by the project's tests.
        #
        # The upstream PyPI package name in requirements.txt is `django-with-asserts`,
        # which provides the `with_asserts` module.
        withAssertsSrc = pkgs.runCommand "with-asserts-src" { } ''
          mkdir -p $out/with_asserts
          cat > $out/with_asserts/__init__.py <<'PY'
          """Minimal compatibility shim for the `with_asserts` test helper.

          The project test-suite only relies on AssertHTMLMixin.assertHTML (as a
          context-manager) and AssertHTMLMixin.assertNotHTML.
          """
          from .mixin import AssertHTMLMixin  # noqa: F401
          PY

          cat > $out/with_asserts/mixin.py <<'PY'
          from __future__ import annotations

          from contextlib import contextmanager

          from lxml import html


          class AssertHTMLMixin:
              """Mixin providing simple CSS-selector assertions for Django responses."""

              def _parse_response(self, response):
                  content = getattr(response, "content", response)
                  if isinstance(content, bytes):
                      charset = getattr(response, "charset", None) or "utf-8"
                      try:
                          text = content.decode(charset, errors="replace")
                      except Exception:
                          text = content.decode("utf-8", errors="replace")
                  else:
                      text = str(content)
                  return html.fromstring(text)

              def _select(self, tree, selector: str):
                  # The expected API is CSS selectors (used across the test-suite).
                  try:
                      return tree.cssselect(selector)
                  except Exception:
                      # Fallback: allow XPath in case a caller passes it.
                      return tree.xpath(selector)

              @contextmanager
              def assertHTML(self, response, selector: str, msg: str | None = None):
                  tree = self._parse_response(response)
                  matches = self._select(tree, selector)
                  if not matches:
                      self.fail(msg or f"Expected selector to match: {selector}")
                  yield matches

              def assertNotHTML(self, response, selector: str, msg: str | None = None):
                  tree = self._parse_response(response)
                  matches = self._select(tree, selector)
                  if matches:
                      self.fail(msg or f"Expected selector not to match: {selector}")
          PY
        '';

        # Core Python environment for running the app + tests.
        pythonEnv = python.withPackages (ps: [
          ps.django
          ps.coverage
          ps.faker
          ps.lxml
          ps.cssselect
          ps.pillow
          ps."python-dotenv"
          ps."django-widget-tweaks"
          ps.libgravatar
        ]);

        # Helper used by all entrypoint scripts: locate project root (works when
        # called from subdirectories).
        findRoot = ''
          find_root() {
            local dir="$PWD"
            while [ "$dir" != "/" ]; do
              if [ -f "$dir/manage.py" ]; then
                echo "$dir"
                return 0
              fi
              dir="$(dirname "$dir")"
            done
            echo "Error: could not locate project root (manage.py not found in parent dirs)." >&2
            exit 1
          }
          cd "$(find_root)"
        '';

        commonEnv = ''
          export PYTHONUNBUFFERED=1
          export DJANGO_SETTINGS_MODULE=clarify.settings
          export PYTHONPATH="${withAssertsSrc}:$PYTHONPATH"
        '';

        initScript = pkgs.writeShellApplication {
          name = "clarify-init";
          runtimeInputs = [ pkgs.coreutils pythonEnv ];
          text = ''
            set -euo pipefail
            ${findRoot}
            ${commonEnv}

            echo "==> Applying database migrations"
            python manage.py migrate --noinput

            echo "==> Seeding the database"
            # Make seeding idempotent: the project's seed command always creates
            # a '@staffuser' account, so remove it first if it exists.
            python manage.py shell -c "from tickets.models import User; User.objects.filter(username='@staffuser').delete()" >/dev/null 2>&1 || true
            python manage.py seed

            echo
            echo "Initialisation complete."
            echo "- Run the app:     nix run .#run"
            echo "- Run tests:       nix run .#tests"
            echo "- Unseed database: nix run .#unseed"
          '';
        };

        runScript = pkgs.writeShellApplication {
          name = "clarify-run";
          runtimeInputs = [ pkgs.coreutils pythonEnv ];
          text = ''
            set -euo pipefail
            ${findRoot}
            ${commonEnv}

            # Ensure the local sqlite database schema is up to date.
            python manage.py migrate --noinput

            echo "Starting Django development server at http://localhost:8000"
            exec python manage.py runserver 0.0.0.0:8000
          '';
        };

        testsScript = pkgs.writeShellApplication {
          name = "clarify-tests";
          runtimeInputs = [ pkgs.coreutils pythonEnv ];
          text = ''
            set -euo pipefail
            ${findRoot}
            ${commonEnv}

            REPORT_DIR="$PWD/.coverage-reports"
            rm -rf "$REPORT_DIR"
            mkdir -p "$REPORT_DIR"

            echo "==> Running tests with coverage"
            export COVERAGE_FILE="$REPORT_DIR/.coverage"
            coverage run manage.py test

            echo
            echo "==> Coverage summary"
            coverage report -m

            echo
            echo "==> Writing coverage reports"
            coverage html -d "$REPORT_DIR/html"
            coverage xml -o "$REPORT_DIR/coverage.xml"

            echo
            echo "Coverage output written to:"
            echo "- HTML report:  $REPORT_DIR/html/index.html"
            echo "- XML report:   $REPORT_DIR/coverage.xml"
            echo "- Data file:    $REPORT_DIR/.coverage"
          '';
        };

        seedScript = pkgs.writeShellApplication {
          name = "clarify-seed";
          runtimeInputs = [ pkgs.coreutils pythonEnv ];
          text = ''
            set -euo pipefail
            ${findRoot}
            ${commonEnv}

            python manage.py migrate --noinput

            # Make seeding robust if run multiple times.
            python manage.py shell -c "from tickets.models import User; User.objects.filter(username='@staffuser').delete()" >/dev/null 2>&1 || true

            python manage.py seed || {
              echo "Seed command failed; attempting a second run after cleanup..." >&2
              python manage.py shell -c "from tickets.models import User; User.objects.filter(username='@staffuser').delete()" >/dev/null 2>&1 || true
              python manage.py seed
            }

            echo "Database seeded (idempotent)."
          '';
        };

        unseedScript = pkgs.writeShellApplication {
          name = "clarify-unseed";
          runtimeInputs = [ pkgs.coreutils pythonEnv ];
          text = ''
            set -euo pipefail
            ${findRoot}
            ${commonEnv}

            python manage.py unseed
            echo "Database unseeded. You can reseed with: nix run .#seed"
          '';
        };

      in
      {
        apps = {
          init = { type = "app"; program = "${initScript}/bin/clarify-init"; };
          run = { type = "app"; program = "${runScript}/bin/clarify-run"; };
          tests = { type = "app"; program = "${testsScript}/bin/clarify-tests"; };
          seed = { type = "app"; program = "${seedScript}/bin/clarify-seed"; };
          unseed = { type = "app"; program = "${unseedScript}/bin/clarify-unseed"; };
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
          ];

          shellHook = ''
            ${commonEnv}

            echo
            echo "Clarify Django dev shell"
            echo
            echo "Available entrypoints:"
            echo "  nix run .#init    - migrate DB + seed demo data"
            echo "  nix run .#run     - start Django dev server on http://localhost:8000"
            echo "  nix run .#tests   - run test suite + write coverage to ./.coverage-reports/"
            echo "  nix run .#seed    - seed demo data (safe to re-run)"
            echo "  nix run .#unseed  - flush DB (removes all data)"
            echo
          '';
        };

        formatter = pkgs.nixpkgs-fmt;
      });
}