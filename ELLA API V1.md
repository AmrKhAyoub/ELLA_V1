# ELLA API Documentation

  

This document provides a comprehensive and detailed reference for all the API endpoints available in the ELLA system. The endpoints are categorized by their respective applications and functionalities.

  

---

  

## 🔐 Authentication Overview

  

Most endpoints in this API require authentication using JSON Web Tokens (JWT).

When an endpoint requires authentication, you must include the following header in your HTTP request:

  

```http

Authorization: Bearer <your_access_token>

```

  

---

  
## 1. Authentication & Authorization

### 1.1 Register New User

**URL:** `/api/accounts/register/`

**Method:** `POST`

**Auth Required:** No

**Description:** Creates a new user account in the system. A default avatar is automatically generated based on the username and email if not provided.

**Request Body:**

JSON

```
{
    "username": "johndoe",
    "email": "johndoe@example.com",
    "password": "StrongPassword123!"
}
```

**Success Response (201 Created):**

JSON

```
{
    "message": "User created successfully",
    "user_id": 1
}
```

### 1.2 Login (Obtain JWT Tokens)

**URL:** `/api/accounts/login/`

**Method:** `POST`

**Auth Required:** No

**Description:** Authenticates a user using their email and password, returning both an access token (short-lived) and a refresh token (long-lived). Note: The authentication field is `email`.

**Request Body:**

JSON

```
{
    "email": "johndoe@example.com",
    "password": "StrongPassword123!"
}
```

**Success Response (200 OK):**

JSON

```
{
    "refresh": "eyJhbGciOiJIUzI1Ni...",
    "access": "eyJhbGciOiJIUzI1Ni..."
}
```

### 1.3 Refresh Token

**URL:** `/api/accounts/token/refresh/`

**Method:** `POST`

**Auth Required:** No (Requires a valid refresh token in the request body)

**Description:** Generates a new access token using a valid refresh token.

**Request Body:**

JSON

```
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90..."
}
```

**Success Response (200 OK):**

JSON

```
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90..."
}
```

### 1.4 Logout

**URL:** `/api/accounts/logout/`

**Method:** `POST`

**Auth Required:** Yes

**Description:** Logs out the currently authenticated user by blacklisting the provided refresh token so it can no longer be used to generate new access tokens.

**Request Body:**

JSON

```
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90..."
}
```

**Success Response (205 Reset Content):**

JSON

```
{
    "message": "Successfully logged out."
}
```

**Error Response (400 Bad Request):**

JSON

```
{
    "error": "Invalid token or token already blacklisted."
}
```

## 2. User Profile Management

### 2.1 Retrieve User Profile

**URL:** `/api/accounts/profile/`

**Method:** `GET`

**Auth Required:** Yes

**Description:** Retrieves the complete profile details of the currently authenticated user.

**Request Body:** None

**Success Response (200 OK):**

JSON

```
{
    "id": 1,
    "username": "johndoe",
    "email": "johndoe@example.com",
    "avatar": "/media/avatars/johndoe.png",
    "current_level": "A1",
    "target_level": "B2",
    "learning_goal": "To travel and work abroad",
    "gender": "M",
    "birth_date": "1995-08-15",
    "study_level": "BAC",
    "study_field": 3,
    "has_taken_initial_assessment": false
}
```

### 2.2 Update User Profile

**URL:** `/api/accounts/profile/`

**Method:** `PATCH` (Recommended for partial updates) / `PUT`

**Auth Required:** Yes

**Description:** Allows the authenticated user to update their profile information. Users can send only the fields they want to update (Partial Update) when using `PATCH`. The `email` and `id` fields are strictly read-only.

**Request Body (Example - updating learning goal and target level):**

JSON

```
{
    "learning_goal": "Improve communication skills",
    "target_level": "C1"
}
```

**Success Response (200 OK):**

JSON

```
{
    "id": 1,
    "username": "johndoe",
    "email": "johndoe@example.com",
    "avatar": "/media/avatars/johndoe.png",
    "current_level": "A1",
    "target_level": "C1",
    "learning_goal": "Improve communication skills",
    "gender": "M",
    "birth_date": "1995-08-15",
    "study_level": "BAC",
    "study_field": 3,
    "has_taken_initial_assessment": false
}
```

**Error Response (400 Bad Request - E.g., target level is not higher than current level):**

JSON

```
{
    "target_level": [
        "Target level must be higher than current level."
    ]
}
```

### 2.3 Delete User Account

**URL:** `/api/accounts/profile/`

**Method:** `DELETE`

**Auth Required:** Yes

**Description:** Permanently deletes the account of the currently authenticated user from the database.

**Request Body:** None

**Success Response (204 No Content):**

_(No content is returned in the response body upon successful deletion)_

### 2.4 Change Password

**URL:** `/api/accounts/change-password/`

**Method:** `PUT` / `PATCH`

**Auth Required:** Yes

**Description:** Allows the authenticated user to securely change their password by providing their current (old) password and a new password.

**Request Body:**

JSON

```
{
    "old_password": "StrongPassword123!",
    "new_password": "NewSecurePassword456@"
}
```

**Success Response (200 OK):**

JSON

```
{
    "message": "Password updated successfully."
}
```

**Error Response (400 Bad Request - Wrong old password):**

JSON

```
{
    "old_password": [
        "Old password is not correct."
    ]
}
```
  
  

---

  

## 3. Location Tracker

  

### 3.1 Update User Location

  

* **URL:** `/api/tracker/update-location/`

* **Method:** `POST`

* **Auth Required:** Yes

* **Description:** Receives the user's current GPS coordinates. If coordinates are omitted, the backend falls back to IP-based location tracking. This task is processed asynchronously via Celery.

* **Request Body (Optional coordinates):**

```json

{

    "latitude": 40.7128,

    "longitude": -74.0060

}

  

```

  
  

* **Success Response (202 Accepted):**

```json

{

    "message": "Location received. Processing in background..."

}

  

```

  
  
  

---

  

## 4. Notifications

  

### 4.1 Get Notifications List

  

* **URL:** `/api/notifications/`

* **Method:** `GET`

* **Auth Required:** Yes

* **Description:** Retrieves all notifications for the authenticated user along with the total count of unread notifications.

* **Example Request:** (No body, just `Authorization` header)

* **Success Response (200 OK):**

```json

{

    "unread_count": 1,

    "notifications": [

        {

            "id": 15,

            "title": "Welcome to ELLA!",

            "message": "Start your first chat session with your AI tutor.",

            "is_read": false,

            "created_at": "2023-10-25T10:30:00Z"

        }

    ]

}

  

```

  
  
  

### 4.2 Mark Notifications as Read

  

* **URL:** `/api/notifications/mark-read/`

* **Method:** `POST`

* **Auth Required:** Yes

* **Description:** Marks all unread notifications for the authenticated user as read.

* **Example Request:** (No body, just `Authorization` header)

* **Success Response (200 OK):**

```json

{

    "message": "All notifications marked as read."

}

  

```

  
  
  

### 4.3 WebSocket Connection (Live Notifications)

  

* **URL:** `ws://<your_domain>/ws/notifications/?token=<access_token>`

* **Protocol:** `WebSocket` (ws:// or wss://)

* **Auth Required:** Yes (via query parameter `token`)

* **Description:** Establishes a persistent, real-time connection for pushing live notifications to the user interface.

  

---

  
## 5. Chat Sessions Management

---

### 5.1 List and Create Chat Sessions

**URL:** `/api/chats/sessions/`

**Method:** `GET` | `POST`

**Auth Required:** Yes

**Description:**

- **GET:** Lists all chat sessions belonging to the authenticated user, ordered by the newest first. Supports optional filtering by topic.
    
- **POST:** Creates a new chat session.
    

**Query Parameters (GET):**

- `topic` (string, optional): Filter sessions where the topic contains the specified string. Example: `?topic=Grammar`
    

**POST Request Body:**

JSON

```
{
    "topic": "Present Continuous Practice"
}
```

**GET Success Response (200 OK):**

JSON

```
[
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "topic": "Present Continuous Practice",
        "created_at": "2023-10-25T11:00:00Z"
    },
    {
        "id": "98765432-abcd-efgh-ijkl-1234567890ab",
        "topic": "Vocabulary: Travel",
        "created_at": "2023-10-24T09:15:00Z"
    }
]
```

**POST Success Response (201 Created):**

JSON

```
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "topic": "Present Continuous Practice",
    "created_at": "2023-10-25T11:00:00Z"
}
```

### 5.2 Retrieve, Update, and Delete a Specific Session

**URL:** `/api/chats/sessions/<session_id>/`

**Method:** `GET` | `PATCH` (or `PUT`) | `DELETE`

**Auth Required:** Yes

**Description:**

- **GET:** Retrieves the details of a specific session.
    
- **PATCH/PUT:** Updates the session's details (e.g., changing the topic title).
    
- **DELETE:** Permanently deletes the session. **Note:** This will automatically delete all messages associated with this session.
    

**PATCH Request Body:**

JSON

```
{
    "topic": "Advanced Present Continuous Practice"
}
```

**PATCH/GET Success Response (200 OK):**

JSON

```
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "topic": "Advanced Present Continuous Practice",
    "created_at": "2023-10-25T11:00:00Z"
}
```

**DELETE Success Response (204 No Content):**

JSON

```
// No body returned. The session and all related messages have been deleted.
```

## 6. Chat Messages & AI Interaction

This group handles fetching the message history of a specific session and sending new messages to the AI.

### 6.1 Get Session Messages

**URL:** `/api/chats/sessions/<session_id>/messages/`

**Method:** `GET`

**Auth Required:** Yes

**Description:**

Retrieves the complete, chronological history of messages (both User and AI) for a specific session.

**Example Request:**

`GET /api/chats/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/messages/`

**Success Response (200 OK):**

JSON

```
[
    {
        "id": 101,
        "sender": "user",
        "content_text": "Hello AI tutor!",
        "audio_file": null,
        "timestamp": "2023-10-25T11:05:00Z"
    },
    {
        "id": 102,
        "sender": "ai",
        "content_text": "Hello! How can I help you improve your English today?",
        "audio_file": null,
        "timestamp": "2023-10-25T11:05:03Z"
    }
]
```

### 6.2 Send Message to AI

**URL:** `/api/chats/sessions/<session_id>/send/`

**Method:** `POST`

**Auth Required:** Yes

**Description:**

Submits a user message to the specified session, processes it through the AI service using the session's conversational history as context, and returns both the saved user message and the newly generated AI response.

**Request Body:**

JSON

```
{
    "content_text": "Can you explain the difference between 'much' and 'many'?"
}
```

**Success Response (201 Created):**

JSON

```
{
    "user_message": {
        "id": 103,
        "sender": "user",
        "content_text": "Can you explain the difference between 'much' and 'many'?",
        "audio_file": null,
        "timestamp": "2023-10-25T11:10:00Z"
    },
    "ai_message": {
        "id": 104,
        "sender": "ai",
        "content_text": "Of course! We use 'many' with countable nouns (like apples, cars) and 'much' with uncountable nouns (like water, time).",
        "audio_file": null,
        "timestamp": "2023-10-25T11:10:04Z"
    }
}
```

**Error Responses:**

- **400 Bad Request:** If `content_text` is missing.
    
- **404 Not Found:** If the `session_id` does not exist or does not belong to the authenticated user.
    
- **503 Service Unavailable:** If the AI service fails to generate a response.

---
## 7. Analytics (Mistakes & Progress)

  ---

### 7.1 List Educational Mistakes

  

* **URL:** `/api/analytics/mistakes/`

* **Method:** `GET`

* **Auth Required:** Yes

* **Query Parameters:**

* `category` (Optional): Filter mistakes by specific category. Allowed values: `GRAMMAR`, `SPELLING`, `VOCABULARY`, `PUNCTUATION`.

  
  

* **Description:** Retrieves a list of linguistic mistakes made by the user during chat sessions, extracted by the AI tutor, along with corrections and explanations.

* **Example Request:** `GET /api/analytics/mistakes/?category=GRAMMAR`

* **Success Response (200 OK):**

```json

{

    "count": 1,

    "next": null,

    "previous": null,

    "results": [

        {

            "id": 50,

            "wrong_text": "He go to school.",

            "corrected_text": "He goes to school.",

            "category": "GRAMMAR",

            "explanation": "Use 'goes' for third-person singular in the Present Simple tense.",

            "created_at": "2023-10-25T11:15:00Z"

        }

    ]

}

  

```

## 8. Assessments (Onboarding & Grading)

  

### 8.1 Start or Resume Assessment Session

  

**URL:** `/api/assessments/session/`

  

**Method:** `GET`

  

**Auth Required:** Yes

  

**Description:** Initializes a new onboarding assessment session for the user or resumes an existing `in_progress` session. It automatically checks if the existing session is older than 7 days; if so, it discards the expired draft and starts a fresh one. If the user has already completed the assessment, it returns a 400 Bad Request.

  

**Example Request:** `GET /api/assessments/session/`

  

**Success Response (200 OK):**

  

```json

{

    "message": "Resuming your ongoing assessment.",

    "session": {

        "id": 42,

        "status": "in_progress",

        "current_step": 3,

        "draft_data": {

            "step_1": {

                "name": "Leo",

                "age_group": "18-24",

                "native_language": "Spanish"

            },

            "step_2": {

                "overall_rating": 6,

                "reading_skill": 7

            }

        },

        "final_score": null,

        "assigned_level": null,

        "updated_at": "2023-10-25T10:15:30Z"

    }

}

  

```

  

**Error Response (400 Bad Request) - Already Completed:**

  

```json

{

    "message": "You have already completed the assessment."

}

  

```

  

---

  

### 8.2 Get Academic Assessment Questions

  

**URL:** `/api/assessments/questions/`

  

**Method:** `GET`

  

**Auth Required:** Yes

  

**Description:** Retrieves the list of academic questions (CEFR A1-C1) required for Step 6 of the assessment. **Note:** The `correct` answer index and `explanation` fields are intentionally stripped from the backend payload to prevent cheating on the client side.

  

**Example Request:** `GET /api/assessments/questions/`

  

**Success Response (200 OK):**

  

```json

[

    {

        "id": 1,

        "level": "A1",

        "question": "She __________ to the gym every day.",

        "options": [

            "go",

            "goes",

            "going",

            "gone"

        ]

    },

    {

        "id": 2,

        "level": "A1",

        "question": "I want to buy some fresh bread. Let's go to the __________.",

        "options": [

            "library",

            "bakery",

            "pharmacy",

            "museum"

        ]

    }

]

  

```

  

---

  

### 8.3 Save Step Progress (Incremental Save)

  

**URL:** `/api/assessments/save-step/`

  

**Method:** `POST`

  

**Auth Required:** Yes

  

**Description:** Incrementally saves the user's answers for a specific assessment step (1 to 7) into the session's `draft_data` JSON field. Automatically increments the `current_step` counter on the server.

  

**POST Request Body:**

  

```json

{

    "step_number": 3,

    "step_data": {

        "interests": ["📚 Reading", "🎬 Movies & TV", "🎮 Tech & Gaming"],

        "sub_interests": {

            "🎮 Tech & Gaming": ["PC gaming (Steam, MMOs)", "Programming / Coding"]

        }

    }

}

  

```

  

**Success Response (200 OK):**

  

```json

{

    "message": "Step 3 saved successfully.",

    "current_step": 4

}

  

```

  

**Error Response (404 Not Found) - No Active Session:**

  

```json

{

    "error": "No active assessment session found."

}

  

```

  

---

  

### 8.4 Submit Assessment and Generate Results

  

**URL:** `/api/assessments/submit/`

  

**Method:** `POST`

  

**Auth Required:** Yes

  

**Description:** Finalizes the assessment session. It grades the academic answers stored in the `step_6` draft data, calculates the final score out of 10, assigns a CEFR English level based on the result, marks the session as `completed`, and updates the user's profile flag (`has_taken_initial_assessment` = True).

  

**POST Request Body:**

  

*(Empty Body `{}` — the server uses the previously saved draft data)*

  

**Example Request:** `POST /api/assessments/submit/`

  

**Success Response (200 OK):**

  

```json

{

    "message": "Assessment completed successfully!",

    "final_score": 8,

    "level": "Advanced (CEFR C1)",

    "roadmap_ready": true

}

  

```

  

**Error Response (400 Bad Request) - Missing or Expired Session:**

  

```json

{

    "error": "Session expired. Please restart the assessment."

}

```