# IDEA PRO MAX — Event Experience Platform

## Setup

1. Create and activate a virtual environment (venv)
2. Install dependencies
3. Run migrations
4. Create a superuser
5. Run the server

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pip install django
python -m pip install Pillow
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open: http://127.0.0.1:8000/
