# Clarify - Local Development Setup

This guide explains how to run Clarify locally for development and testing.

Clarify is a Django application developed with Python 3.12. You can set it up either with **Nix** (recommended if you already use Nix) or with a standard Python virtual environment.

> **Do not commit real credentials or secrets.**
> Store local configuration in a `.env` file, which should remain excluded from Git.

---

## Prerequisites

For the standard Python setup, install:

- Python 3.12
- `pip`
- `venv` support for your Python installation
- Git

For the Nix setup, install:

- Nix with flakes enabled

The included `flake.nix` supports:

- x86_64 Linux
- Intel macOS
- Apple Silicon macOS

---

## Option 1: Setup with Nix

From the repository root, initialise the local database and seed it with demo data:

```bash
nix run .#init
```

This will:

1. create/apply the Django database migrations;
2. seed the local SQLite database with demo users, tickets, comments and issue data.

Start the development server with:

```bash
nix run .#run
```

The application will be available at:

```text
http://localhost:8000
```

### Other Nix commands

Run the test suite and generate an HTML coverage report:

```bash
nix run .#tests
```

The coverage report is written to:

```text
coverage_html/index.html
```

Seed the database:

```bash
nix run .#seed
```

Remove seeded/local database data:

```bash
nix run .#unseed
```

Open the development shell directly:

```bash
nix develop
```

The development shell includes the Python environment and dependencies required by the project.

---

## Option 2: Setup with Python and `venv`

### 1. Create a virtual environment

From the repository root:

```bash
python3.12 -m venv venv
```

Activate it on macOS or Linux:

```bash
source venv/bin/activate
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If `python3.12` is not available as a command, use the command that points to your Python 3 installation, such as `python3` or `python`.

You can check the active version with:

```bash
python --version
```

Python 3.12 is recommended because it is the version used by the project's CI configuration.

### 2. Install dependencies

Upgrade `pip` and install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

For normal local development, Clarify can run without configuring its email or scheduled-task integrations.

If you want to configure those integrations, create a `.env` file in the repository root.

A suitable template is:

```dotenv
# Django
SECRET_KEY=replace-with-a-secret-value
SITE_URL=http://localhost:8000

# Scheduled task authentication
CRON_TOKEN=replace-with-a-random-token

# Outgoing email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@example.com

# Incoming email (IMAP)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@example.com
IMAP_PASSWORD=your-app-password
```

Do not use production credentials in a committed file.

For local development, Clarify uses its built-in development Django secret if `SECRET_KEY` is not provided. Production deployments should always provide their own secret through the environment.

### 4. Apply database migrations

```bash
python manage.py migrate
```

Clarify uses SQLite for local development. The database is created as `db.sqlite3` in the project root.

### 5. Seed demo data

```bash
python manage.py seed
```

The seed command creates demo users and a substantial set of generated tickets, comments and issue data for development.

The predefined demo accounts include:

| Role               | Username      |
| ------------------ | ------------- |
| Student            | `@johndoe`    |
| Student            | `@janedoe`    |
| Student            | `@charlie`    |
| Student            | `@student001` |
| Staff              | `@staff001`   |
| Staff              | `@staff002`   |
| Local seeded admin | `@admin`      |

The seeded development password is:

```text
Password123
```

These accounts are intended for local/demo data only. Do not use the seeded admin credentials for a production deployment.

### 6. Start the development server

```bash
python manage.py runserver
```

Then open:

```text
http://localhost:8000
```

---

## Running the Tests

Run the Django test suite with:

```bash
python manage.py test
```

To run the suite with coverage:

```bash
coverage run manage.py test
coverage report -m
```

The GitHub Actions CI workflow requires at least **99% code coverage**.

To generate a browsable HTML coverage report locally:

```bash
coverage run --branch manage.py test
coverage html -d coverage_html
```

Then open:

```text
coverage_html/index.html
```

---

## Email Integration

Clarify supports both outgoing and incoming email.

### Outgoing email

Outgoing email uses SMTP. By default the application expects Gmail-compatible settings:

```dotenv
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
```

If you use Gmail with two-step verification, use a Google **App Password** rather than your normal Google account password.

### Incoming email

Incoming email processing uses IMAP:

```dotenv
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@example.com
IMAP_PASSWORD=your-app-password
```

If `IMAP_USER` and `IMAP_PASSWORD` are not set, Clarify falls back to `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`.

Run the inbox-processing command manually with:

```bash
python manage.py check_inbox
```

Email configuration is not required to run the core application or the automated test suite.

---

## Scheduled Tasks

Clarify exposes authenticated endpoints for scheduled maintenance tasks.

The configured task endpoints include:

```text
/tasks/check-inbox/
/tasks/close-inactive/
```

Requests to these endpoints must provide the configured cron token in the `X-CRON-TOKEN` header.

Set a local token with:

```dotenv
CRON_TOKEN=replace-with-a-random-token
```

For example:

```bash
curl -X POST \
  -H "X-CRON-TOKEN: your-token" \
  http://localhost:8000/tasks/close-inactive/
```

The deployed project uses GitHub Actions to call these endpoints on a schedule. Store the production token as a GitHub Actions secret and as an environment variable on the deployed application; do not put the token directly in workflow files or source code.

---

## Resetting Local Data

To remove the seeded/local data using the provided management command:

```bash
python manage.py unseed
```

With Nix:

```bash
nix run .#unseed
```

You can then recreate the development data with:

```bash
python manage.py seed
```

or:

```bash
nix run .#seed
```

---

## Useful Development Commands

```bash
# Apply database migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Start the development server
python manage.py runserver

# Seed demo data
python manage.py seed

# Remove seeded/local data
python manage.py unseed

# Process the configured inbox manually
python manage.py check_inbox

# Run tests
python manage.py test

# Run tests with coverage
coverage run manage.py test
coverage report -m
```

---

## Production Notes

The repository includes production-specific Django settings for the deployed PythonAnywhere instance.

When Django detects the PythonAnywhere production environment, it enables production security settings including HTTPS redirection, secure cookies and HSTS, and expects `SECRET_KEY` to be supplied through the environment.

A production deployment should provide at least the environment variables required for the features it uses, including:

```text
SECRET_KEY
CRON_TOKEN
SITE_URL
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
IMAP_USER
IMAP_PASSWORD
```

Never deploy using demo credentials or a development secret key for privileged accounts.

---

## Troubleshooting

### `ModuleNotFoundError`

Make sure your virtual environment is active and reinstall the dependencies:

```bash
python -m pip install -r requirements.txt
```

### Database schema errors

Apply all migrations:

```bash
python manage.py migrate
```

### Demo data is missing

Run:

```bash
python manage.py seed
```

### Email processing fails

Check that the SMTP/IMAP environment variables are configured correctly and that any Gmail App Password is valid.

### Nix command cannot find the project

Run the Nix commands from the repository itself, or from a subdirectory whose parent contains `manage.py`.

---

## Further Documentation

For the project overview, live demo, engineering highlights and contributor information, see the main [`README.md`](../README.md).
