# Queue Cure '26

Queue Cure '26 is a clinic queue system for replacing paper tokens with a live digital queue.

This repo is being built module by module. The current brick is the project foundation:

- `backend/` contains the Django project.
- `frontend/` contains Django templates and static files.
- `start.txt` is kept local and ignored by Git.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python manage.py check
```

Before running in production, set a real `SECRET_KEY`, database URL, and secure cookie settings in the environment.
