# ATO CRM (Django)

A Django-based internal CRM system with request workflows, leave tracking, finance approvals, payroll tools, and internal letters.

## Features

- Core request workflow with role-based approvals
- Leave request management
- Finance module:
  - Payroll dashboard
  - Salary advances with multi-level approval
  - Loans with approval flow
  - Expenses, incomes, budgets, bank accounts
- Internal letter management
- Django Admin customization

## Tech Stack

- Python 3
- Django 6
- Django REST Framework
- SQLite (default)

## Project Structure

- core: Main workflow, profiles, departments, approvals
- finance: Payroll, salary advances, loans, accounting modules
- internal_letter: Internal communications module
- templates: Shared and app templates
- static: Project static assets

## Local Setup (Windows)

1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r req.txt
```

3. Run migrations

```powershell
python manage.py migrate
```

4. Start development server

```powershell
python manage.py runserver
```

5. Open in browser

- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Finance Payroll: http://127.0.0.1:8000/finance/payroll/

## Useful Commands

```powershell
python manage.py check
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Notes

- Default DB is SQLite.
- Keep environment-specific secrets out of source control.
- If deploying, configure ALLOWED_HOSTS, static/media paths, and production settings.

## License

Private/internal project.
