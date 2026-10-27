# EvacuaLink

EvacuaLink is a modular Django project for evacuation management using PostgreSQL only.

## Requirements

- Python 3.10+
- PostgreSQL running locally on port `5432`
- pgAdmin4 or another PostgreSQL administration tool
- Database configuration (via `.env`):
  - Database: `evacualink_db`
  - User: `postgres` (or your local PostgreSQL role)
  - Password: `<your_postgres_password>`
  - Host: `localhost`
  - Port: `5432`

## Full folder structure

```text
EvacuaLink/
├── manage.py
├── .env
├── requirements.txt
├── README.md
├── evacualink/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── evacuation_centers/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── evacuees/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── families/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── reports/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── emergency/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
└── mapping/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── urls.py
    ├── views.py
    └── migrations/
        └── __init__.py
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Direct dependency installation requested:

```bash
pip install psycopg2-binary
```

This project also uses `python-decouple` to read database credentials from `.env`:

```bash
pip install python-decouple
```

## PostgreSQL setup

### pgAdmin4 setup

1. Open pgAdmin4.
2. Connect to your local PostgreSQL server.
3. Confirm the server connection uses:
   - Host: `localhost`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres`
4. Set a strong password for your PostgreSQL user and save it to your local `.env` file.
5. Create the database:
   - Right-click `Databases`.
   - Select `Create` > `Database`.
   - Set database name to `evacualink_db`.
   - Set owner to `postgres`.
   - Click `Save`.

You can also create the database using SQL:

Create the PostgreSQL database before running migrations:

```sql
CREATE DATABASE evacualink_db;
```

If you need to set or update your PostgreSQL role password:

```sql
ALTER USER postgres WITH PASSWORD 'your_secure_password';
```

## Environment variables

Database credentials are stored in `.env` and loaded by `python-decouple` in `evacualink/settings.py`.

Required `.env` format (see `.env.example`):

```env
DB_NAME=evacualink_db
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
```

The Django database configuration in `evacualink/settings.py` uses PostgreSQL only:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    }
}
```

SQLite is not configured or used anywhere in this project.

## Migrations

Run:

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Create an administrator:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

## Verify PostgreSQL integration

Run Django's built-in checks:

```bash
python manage.py check
```

Verify the database connection and migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

If these commands complete successfully, Django is connected to PostgreSQL and all models migrate properly.

## Troubleshooting guide

### Connection refused

Symptoms:

```text
could not connect to server: Connection refused
```

Fixes:

1. Start PostgreSQL service.
2. Confirm PostgreSQL listens on port `5432`.
3. Confirm `HOST = "localhost"` and `PORT = "5432"` in `evacualink/settings.py`.

### Authentication failed

Symptoms:

```text
FATAL: password authentication failed for user "postgres"
```

Fixes:

1. Confirm the PostgreSQL password matches the `DB_PASSWORD` set in your `.env` file.
2. Reset the password if needed:

```sql
ALTER USER postgres WITH PASSWORD 'your_secure_password';
```

3. Confirm `pg_hba.conf` allows password authentication for local connections.
4. Restart PostgreSQL after changing `pg_hba.conf` or authentication settings.
5. Confirm `.env` contains your correct `DB_PASSWORD`.
6. This error indicates that PostgreSQL rejected the credentials specified in your `.env` file.

### Database does not exist

Symptoms:

```text
FATAL: database "evacualink_db" does not exist
```

Fix:

```sql
CREATE DATABASE evacualink_db;
```

### psycopg2 import error

Symptoms:

```text
Error loading psycopg2 or psycopg module
```

Fix:

```bash
pip install psycopg2-binary
```

### Migration dependency errors with custom user model

Fixes:

1. Keep `AUTH_USER_MODEL = "users.User"` set before first migration.
2. Run migrations from a clean database if the default auth user table was already created incorrectly.
3. Run:

```bash
python manage.py makemigrations users families evacuation_centers evacuees emergency reports mapping
python manage.py migrate
```
