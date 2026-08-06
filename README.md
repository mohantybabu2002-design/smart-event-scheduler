# Smart Event Scheduler — Step 1: Users & Auth

A backend API (built with FastAPI + PostgreSQL) that will eventually let
multiple users find overlapping free time and book meetings without
double-booking. This is step 1 of the build: user signup/login with
JWT authentication.

## What's in this step

- `app/database.py` — DB connection setup
- `app/models.py` — the `User` table
- `app/schemas.py` — request/response shapes (what the API accepts/returns)
- `app/auth.py` — password hashing + JWT creation/verification
- `app/routers/auth_routes.py` — `/signup`, `/login`, `/me` endpoints
- `app/main.py` — app entry point

## Setup (run this on your own machine)

1. Install PostgreSQL locally (or use Docker: `docker run --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres`)
   and create a database called `scheduler`.

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in real values:
   ```bash
   cp .env.example .env
   ```

4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Open **http://127.0.0.1:8000/docs** — this is FastAPI's auto-generated
   interactive docs page. You can test `/signup`, `/login`, and `/me`
   directly in the browser, no separate tool needed.

## Try it out

1. Go to `/docs`, expand `POST /signup`, click "Try it out", fill in
   name/email/password/timezone, execute. You should get a 200 with
   your user data back (no password_hash visible).
2. Expand `POST /login`, use the same email/password. You'll get back
   an `access_token`.
3. Click the padlock icon (top right of `/docs`) or the one next to
   `GET /me`, paste in your token, and call `/me` — you should see your
   own user info. Try it WITHOUT the token first — you should get a 401.

## Why it's built this way

- **Passwords are hashed with bcrypt** — even if the database leaks,
  raw passwords are never stored or visible.
- **JWT tokens instead of server-side sessions** — the server doesn't
  need to remember who's logged in; the token itself proves identity
  and expires after 24h.
- **Schemas separate from models** — the DB `User` model has a
  `password_hash` column, but `UserOut` (what gets returned) simply
  doesn't include it, so it's structurally impossible to leak it by
  accident.

## Next steps (coming up)

- Add `Event`, `Availability`, `Participant` tables
- Build the overlap-detection logic (the core algorithm)
- Add the "find common free slot across multiple users" feature
- Write tests
- Deploy to Render/Railway
