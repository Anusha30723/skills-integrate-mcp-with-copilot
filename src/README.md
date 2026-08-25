# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Create a student account and log in
- Sign up for activities as the authenticated student
- Unregister yourself from activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/auth/register`                                                   | Create a student account                                             |
| POST   | `/auth/login`                                                      | Log in and receive an expiring bearer token                          |
| POST   | `/auth/logout`                                                     | Revoke the current bearer token                                      |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup`                              | Sign up the authenticated student for an activity                    |
| DELETE | `/activities/{activity_name}/unregister`                          | Unregister the authenticated student from an activity                |

Signup and unregister require an `Authorization: Bearer <token>` header.

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

Users, sessions, activities, and registrations are stored in memory, which means data will be reset when the server restarts. Passwords are stored as salted PBKDF2 hashes, and session tokens expire after eight hours or when the user logs out.
