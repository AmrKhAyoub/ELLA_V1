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

## 1. Accounts & Authentication

### 1.1 Register New User

* **URL:** `/api/accounts/register/`
* **Method:** `POST`
* **Auth Required:** No
* **Description:** Creates a new user account and automatically generates a unique avatar.
* **Request Body:**
```json
{
    "username": "student_123",
    "email": "student@example.com",
    "password": "StrongPassword123!"
}

```


* **Success Response (201 Created):**
```json
{
    "message": "User registered successfully.",
    "user": {
        "id": 1,
        "username": "student_123",
        "email": "student@example.com",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=student_123"
    }
}

```



### 1.2 Login (Get JWT Tokens)

* **URL:** `/api/accounts/login/`
* **Method:** `POST`
* **Auth Required:** No
* **Description:** Authenticates a user and returns access and refresh tokens.
* **Request Body:**
```json
{
    "username": "student_123",
    "password": "StrongPassword123!"
}

```


* **Success Response (200 OK):**
```json
{
    "refresh": "eyJhbGciOiJIUzI1Ni...",
    "access": "eyJhbGciOiJIUzI1Ni..."
}

```



---

## 2. Location Tracker

### 2.1 Update User Location

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

## 3. Notifications

### 3.1 Get Notifications List

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



### 3.2 Mark Notifications as Read

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



### 3.3 WebSocket Connection (Live Notifications)

* **URL:** `ws://<your_domain>/ws/notifications/?token=<access_token>`
* **Protocol:** `WebSocket` (ws:// or wss://)
* **Auth Required:** Yes (via query parameter `token`)
* **Description:** Establishes a persistent, real-time connection for pushing live notifications to the user interface.

---

## 4. Chats (AI Tutor)

### 4.1 List and Create Chat Sessions

* **URL:** `/api/chats/sessions/`
* **Method:** `GET` | `POST`
* **Auth Required:** Yes
* **Description:**
* **GET:** Lists all chat sessions belonging to the user.
* **POST:** Creates a new chat session.


* **POST Request Body:**
```json
{
    "topic": "Present Continuous Practice"
}

```


* **POST Success Response (201 Created):**
```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "topic": "Present Continuous Practice",
    "created_at": "2023-10-25T11:00:00Z"
}

```



### 4.2 Get Session Messages

* **URL:** `/api/chats/sessions/<session_id>/messages/`
* **Method:** `GET`
* **Auth Required:** Yes
* **Description:** Retrieves the chronological history of messages (both User and AI) for a specific session.
* **Example Request:** `GET /api/chats/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/messages/`
* **Success Response (200 OK):**
```json
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



### 4.3 Send Message to AI

* **URL:** `/api/chats/sessions/<session_id>/send/`
* **Method:** `POST`
* **Auth Required:** Yes
* **Description:** Submits a user message to the session, processes it through the Groq AI service, and returns both the saved user message and the generated AI response.
* **Request Body:**
```json
{
    "content_text": "Can you explain the difference between 'much' and 'many'?"
}

```


* **Success Response (201 Created):**
```json
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



---

## 5. Analytics (Mistakes & Progress)

### 5.1 List Educational Mistakes

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
## 6. Assessments (Onboarding & Grading)

### 6.1 Start or Resume Assessment Session

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

### 6.2 Get Academic Assessment Questions

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

### 6.3 Save Step Progress (Incremental Save)

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

### 6.4 Submit Assessment and Generate Results

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