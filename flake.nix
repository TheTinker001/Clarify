{
  description = "Clarify (Django) - dev flake with venv + requirements.txt + init/run/tests/seed/unseed";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-darwin" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python312;

        # Native deps commonly needed to build wheels for requirements (e.g. lxml, Pillow)
        nativeLibs = [
          pkgs.stdenv.cc
          pkgs.pkg-config
          pkgs.zlib.dev
          pkgs.openssl.dev
          pkgs.libffi.dev
          pkgs.libxml2.dev
          pkgs.libxslt.dev
        ];

        # In-flake shim for `with_asserts` (kept as a fallback; harmless if pip installs the real thing)
        withAssertsSrc = pkgs.runCommand "with-asserts-src" { } ''
          mkdir -p $out/with_asserts
          cat > $out/with_asserts/__init__.py <<'PY'
          from .mixin import AssertHTMLMixin  # noqa: F401
          PY

          cat > $out/with_asserts/mixin.py <<'PY'
          from __future__ import annotations
          from contextlib import contextmanager
          from lxml import html

          class AssertHTMLMixin:
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
                  try:
                      return tree.cssselect(selector)
                  except Exception:
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
            echo "ERROR: could not locate project root (manage.py not found)." >&2
            exit 1
          }
          cd "$(find_root)"
        '';

        requireProjectRoot = ''
          if [ ! -f manage.py ]; then
            echo "ERROR: manage.py not found. Run from the Django project root." >&2
            exit 1
          fi
          if [ ! -f requirements.txt ]; then
            echo "ERROR: requirements.txt not found in project root." >&2
            exit 1
          fi
        '';

        commonEnv = ''
          export PYTHONUNBUFFERED=1
          export DJANGO_SETTINGS_MODULE=clarify.settings
          export PYTHONPATH="${withAssertsSrc}:${PYTHONPATH:-}"
          export PIP_DISABLE_PIP_VERSION_CHECK=1
        '';

        ensureVenv = ''
          if [ ! -d .venv ]; then
            echo "== Create venv (.venv) =="
            ${python}/bin/python -m venv .venv
          fi

          echo "== Upgrade pip tooling =="
          ./.venv/bin/python -m pip install --upgrade pip setuptools wheel

          echo "== Install Python deps from requirements.txt =="
          ./.venv/bin/python -m pip install -r requirements.txt

          # Ensure coverage is present (in case it's not in requirements.txt)
          ./.venv/bin/python -m pip install --upgrade coverage
        '';

        initScript = pkgs.writeShellApplication {
          name = "clarify-init";
          runtimeInputs = [ pkgs.coreutils python pkgs.git pkgs.sqlite ] ++ nativeLibs;
          text = ''
            set -euo pipefail
            ${findRoot}
            ${requireProjectRoot}
            ${commonEnv}

            ${ensureVenv}

            echo "== Django migrate =="
            ./.venv/bin/python manage.py migrate --noinput

            echo "== Seed database =="
            # Make seeding idempotent: seed always creates @staffuser, so delete it first if it exists
            ./.venv/bin/python manage.py shell -c "from tickets.models import User; User.objects.filter(username='@staffuser').delete()" >/dev/null 2>&1 || true
            ./.venv/bin/python manage.py seed

            echo
            echo "Initialisation complete."
            echo "  nix run .#run     - start server on http://localhost:8000"
            echo "  nix run .#tests   - run tests + HTML coverage to ./coverage_html/"
          '';
        };

        runScript = pkgs.writeShellApplication {
          name = "clarify-run";
          runtimeInputs = [ pkgs.coreutils python pkgs.git pkgs.sqlite ] ++ nativeLibs;
          text = ''
            set -euo pipefail
            ${findRoot}
            ${requireProjectRoot}
            ${commonEnv}

            if [ ! -x ./.venv/bin/python ]; then
              echo "ERROR: .venv not found. Run: nix run .#init" >&2
              exit 1
            fi

            echo "== Django migrate =="
            ./.venv/bin/python manage.py migrate --noinput

            echo "Starting Django development server at http://localhost:8000"
            exec ./.venv/bin/python manage.py runserver 0.0.0.0:8000
          '';
        };

        testsScript = pkgs.writeShellApplication {
          name = "clarify-tests";
          runtimeInputs = [ pkgs.coreutils python pkgs.git pkgs.sqlite ] ++ nativeLibs;
          text = ''
            set -euo pipefail
            ${findRoot}
            ${requireProjectRoot}
            ${commonEnv}

            if [ ! -x ./.venv/bin/python ]; then
              echo "ERROR: .venv not found. Run: nix run .#init" >&2
              exit 1
            fi

            rm -rf coverage_html .coverage

            COV_RC_ARGS=()
            if [ -f .coveragerc ]; then
              COV_RC_ARGS+=(--rcfile=.coveragerc)
            fi

            echo "== Run tests under coverage =="
            ./.venv/bin/coverage run "''${COV_RC_ARGS[@]}" --branch manage.py test

            echo "== Generate HTML coverage report =="
            ./.venv/bin/coverage html "''${COV_RC_ARGS[@]}" -d coverage_html

            echo "OK: HTML coverage report generated at: ./coverage_html/index.html"
          '';
        };

        seedScript = pkgs.writeShellApplication {
          name = "clarify-seed";
          runtimeInputs = [ pkgs.coreutils python pkgs.git pkgs.sqlite ] ++ nativeLibs;
          text = ''
            set -euo pipefail
            ${findRoot}
            ${requireProjectRoot}
            ${commonEnv}

            if [ ! -x ./.venv/bin/python ]; then
              echo "ERROR: .venv not found. Run: nix run .#init" >&2
              exit 1
            fi

            ./.venv/bin/python manage.py migrate --noinput
            ./.venv/bin/python manage.py shell -c "from tickets.models import User; User.objects.filter(username='@staffuser').delete()" >/dev/null 2>&1 || true
            ./.venv/bin/python manage.py seed || true

            echo "Database seeded (safe to re-run)."
          '';
        };

        unseedScript = pkgs.writeShellApplication {
          name = "clarify-unseed";
          runtimeInputs = [ pkgs.coreutils python pkgs.git pkgs.sqlite ] ++ nativeLibs;
          text = ''
            set -euo pipefail
            ${findRoot}
            ${requireProjectRoot}
            ${commonEnv}

            if [ ! -x ./.venv/bin/python ]; then
              echo "ERROR: .venv not found. Run: nix run .#init" >&2
              exit 1
            fi

            ./.venv/bin/python manage.py unseed
            echo "Database unseeded. Reseed with: nix run .#seed"
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
          packages = [ python pkgs.git pkgs.sqlite ] ++ nativeLibs;
          shellHook = ''
            ${commonEnv}
            echo
            echo "Clarify Django dev shell"
            echo "  nix run .#init    - create .venv, pip install -r requirements.txt, migrate, seed"
            echo "  nix run .#run     - start server on http://localhost:8000"
            echo "  nix run .#tests   - tests + HTML coverage to ./coverage_html/"
            echo "  nix run .#seed    - seed demo data (safe to re-run)"
            echo "  nix run .#unseed  - remove all data"
            echo
          '';
        };

        formatter = pkgs.nixpkgs-fmt;
      });
}