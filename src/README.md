# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View current school announcements
- Sign in as a teacher to publish, schedule, edit, and delete announcements

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Start MongoDB on `localhost:27017`, then run from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| POST   | `/auth/login` | Sign in with a JSON body containing `username` and `password`; sets an HttpOnly session cookie |
| GET    | `/auth/check-session` | Return the signed-in teacher using the session cookie |
| POST   | `/auth/logout` | Revoke the current session and clear its cookie |
| GET    | `/announcements` | Public list of currently active announcements |
| GET    | `/announcements/manage` | List all announcements, including scheduled and expired notices; sign-in required |
| POST   | `/announcements` | Create an announcement; sign-in required |
| PUT    | `/announcements/{id}` | Replace an announcement's message and dates; sign-in required |
| DELETE | `/announcements/{id}` | Delete an announcement; sign-in required; returns 204 |

### Announcement Requests

Create and update endpoints accept JSON:

```json
{
   "message": "Activity registration is open!",
   "starts_on": null,
   "expires_on": "2026-12-31"
}
```

Messages must contain 1 to 2,000 characters and cannot be blank. `expires_on` is required;
`starts_on` can be omitted or null for immediate publication. Dates use `YYYY-MM-DD`.
The start date cannot be after expiration. Both dates are inclusive and evaluated
in UTC. Expired announcements remain available to teachers until deleted.
Responses include `id`, `message`, `starts_on`, and `expires_on`.

Only authenticated requests can list nonpublic notices or modify announcements.
Sessions expire after eight hours, are revoked on logout, and use SameSite=Strict
cookies (Secure over HTTPS). Serve the app over HTTPS in production. Mutating
authenticated requests must be same-origin. Invalid requests return 422, missing
sessions return 401, and unknown announcement IDs return 404. Database errors are
logged on the server and return a generic 503 response without internal details.

**Authentication API change:** login now accepts JSON instead of query parameters;
session checks use the cookie instead of a username. Existing integrations must
update their requests. The bundled frontend is updated for both changes.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

3. **Announcements** - Persisted message, optional start date, and required expiration date.

All data is persisted in the `mergington_high` MongoDB database. Initialization
adds example activities, teachers, and a welcome announcement that expires after
30 days. The example announcement is seeded once and is not recreated after deletion.
Session tokens are stored only as hashes, with a MongoDB TTL index for cleanup.
