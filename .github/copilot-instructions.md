# Copilot Instructions for AI Agents

## Project Overview
- This is a Django project named `clarify` with a single main app: `tickets`.
- The project structure follows standard Django conventions, but with some custom subfolders (e.g., `models/`, `views/`, `forms/`, `templates/` inside `tickets/`).
- All business logic, forms, models, and views are organized under `tickets/`.

## Key Components
- **clarify/**: Django project settings, URLs, and WSGI/ASGI entry points.
- **tickets/**: Main app. Contains:
  - `models/`: All model definitions (e.g., `user.py`).
  - `views/`: View logic, split by feature (e.g., `dashboard_view.py`, `log_in_view.py`).
  - `forms/`: Form classes for user input.
  - `templates/`: HTML templates, with `partials/` for reusable components.
  - `management/commands/`: Custom Django management commands (e.g., `seed.py`, `unseed.py`).
  - `tests/`: Organized by feature (forms, models, views, helpers). Uses fixtures for test data.
- **static/**: Static assets (e.g., `custom.css`).

## Developer Workflows
- **Setup**: Use Python 3.12 if possible. Create a virtualenv, install dependencies from `requirements.txt`.
- **Database**: Migrate with `python manage.py migrate`. Seed dev data with `python manage.py seed`.
- **Testing**: Run all tests with `python manage.py test`. Tests are organized by feature in `tickets/tests/`.
- **Fixtures**: Test data is in `tickets/tests/fixtures/` as JSON files.

## Project Conventions
- **App Structure**: Each major feature (auth, dashboard, profile, etc.) has its own view, form, and template file.
- **Templates**: Use `base.html` and `base_content.html` for layout. Partials in `templates/partials/` for shared UI.
- **Custom Management Commands**: Use `seed` and `unseed` for database setup/teardown.
- **Helpers**: Shared logic in `tickets/helpers.py` and `tickets/tests/helpers.py`.
- **Naming**: Files and classes are named by feature and purpose (e.g., `log_in_view.py`, `test_log_in_form.py`).

## Integration Points
- **External Packages**: All dependencies are listed in `requirements.txt`.
- **Reference**: Inspired by https://self-service.kcl.ac.uk.

## Examples
- To add a new feature, create corresponding files in `models/`, `views/`, `forms/`, and `templates/`.
- To add a test, place it in the appropriate subfolder in `tickets/tests/`.

---
For more details, see `README.md` and the `tickets/` app structure.
