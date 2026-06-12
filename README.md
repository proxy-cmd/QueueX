# Queue Cure '26

Queue Cure '26 is a real-time clinic queue management system that replaces paper tokens with a live digital queue.

Patients can view their position in the queue, receptionists can manage tokens, and display screens stay synchronized through real-time updates.

## Project Structure

```text
backend/
    Django project and backend logic

frontend/
    Templates, static files, and UI assets
```

`start.txt` is used locally and is excluded from version control.

---

## Backend Setup

```bash
cd backend

python -m venv .venv

.\.venv\Scripts\python -m pip install -r requirements.txt

Copy-Item .env.example .env

.\.venv\Scripts\python manage.py check
```

Before deployment, configure the environment variables with a valid secret key, database settings, and production security options.

---

## Real-Time Queue Updates

Queue updates are handled using Django Channels and WebSockets.

Endpoint:

```text
/ws/queue/
```

Flow:

```text
Receptionist action
      ↓
Queue data updated
      ↓
WebSocket event sent
      ↓
Connected clients receive update
      ↓
Queue information refreshes instantly
```

This keeps receptionist, patient, and display screens synchronized without requiring page refreshes.

---

## Features

* Digital token generation
* Live queue tracking
* Real-time updates with WebSockets
* Estimated waiting time calculation
* Receptionist queue management
* Patient queue view
* Waiting room display screen

---

## Tech Stack

* Django
* Django Channels
* WebSockets
* SQLite / PostgreSQL
* HTML
* CSS
* JavaScript
