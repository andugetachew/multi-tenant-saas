API Documentation

Base URL

text

http://localhost:8000/api/

Authentication

All endpoints (except login/register) require JWT token in header:



text

Authorization: Bearer <your\_access\_token>

1\. Authentication Endpoints

Register New User/Tenant

http

POST /api/auth/register/

Request Body:



json

{

&#x20; "email": "user@example.com",

&#x20; "password": "securepass123",

&#x20; "password2": "securepass123",

&#x20; "first\_name": "John",

&#x20; "last\_name": "Doe",

&#x20; "organization\_name": "My Company"

}

Response: 201 Created



json

{

&#x20; "id": 1,

&#x20; "email": "user@example.com",

&#x20; "first\_name": "John",

&#x20; "last\_name": "Doe",

&#x20; "organization": 1,

&#x20; "is\_owner": true

}

Login

http

POST /api/auth/login/

Request Body:



json

{

&#x20; "email": "admin@gmail.com",

&#x20; "password": "admin123"

}

Response: 200 OK



json

{

&#x20; "refresh": "eyJhbGciOiJ...",

&#x20; "access": "eyJhbGciOiJ...",

&#x20; "user": {

&#x20;   "id": 2,

&#x20;   "email": "admin@gmail.com",

&#x20;   "organization": 1,

&#x20;   "is\_owner": true

&#x20; }

}

Refresh Token

http

POST /api/auth/token/refresh/

Request Body:



json

{

&#x20; "refresh": "eyJhbGciOiJ..."

}

Response: 200 OK



json

{

&#x20; "access": "eyJhbGciOiJ..."

}

Logout

http

POST /api/auth/logout/

Request Body:



json

{

&#x20; "refresh": "eyJhbGciOiJ..."

}

Response: 205 Reset Content



Get User Profile

http

GET /api/auth/profile/

Response: 200 OK



json

{

&#x20; "id": 2,

&#x20; "email": "admin@gmail.com",

&#x20; "first\_name": "",

&#x20; "last\_name": "",

&#x20; "organization": 1,

&#x20; "is\_owner": true,

&#x20; "role": "member"

}

2\. Organization Endpoints

Get Organization

http

GET /api/organizations/

Headers:



text

X-Organization-ID: 1

Response: 200 OK



json

{

&#x20; "id": 1,

&#x20; "name": "Acme Inc",

&#x20; "plan": "trial",

&#x20; "subscription\_status": "active",

&#x20; "created\_at": "2026-04-28T12:00:00Z"

}

Update Organization

http

PUT /api/organizations/

Request Body:



json

{

&#x20; "name": "New Company Name",

&#x20; "plan": "pro"

}

Invite User

http

POST /api/organizations/invite/

Request Body:



json

{

&#x20; "email": "teammate@example.com"

}

Response: 201 Created



json

{

&#x20; "id": 5,

&#x20; "email": "teammate@example.com",

&#x20; "token": "abc123xyz",

&#x20; "accepted": false

}

3\. Projects Endpoints

List Projects

http

GET /api/projects/

Response: 200 OK



json

\[

&#x20; {

&#x20;   "id": 26,

&#x20;   "name": "Test Project",

&#x20;   "description": "Testing all features",

&#x20;   "status": "active",

&#x20;   "task\_count": 2,

&#x20;   "created\_at": "2026-04-29T00:04:34Z",

&#x20;   "updated\_at": "2026-04-29T00:04:34Z"

&#x20; }

]

Create Project

http

POST /api/projects/

Request Body:



json

{

&#x20; "name": "New Project",

&#x20; "description": "Project description",

&#x20; "tags": "python,django,saas",

&#x20; "status": "active"

}

Response: 201 Created



json

{

&#x20; "id": 29,

&#x20; "name": "New Project",

&#x20; "description": "Project description",

&#x20; "tags": "python,django,saas",

&#x20; "status": "active",

&#x20; "created\_by": 2,

&#x20; "organization": 1

}

Get Single Project

http

GET /api/projects/{id}/

Update Project

http

PUT /api/projects/{id}/

Delete Project

http

DELETE /api/projects/{id}/

4\. Tasks Endpoints

List Tasks

http

GET /api/projects/tasks/

Query Parameters:



project\_id - Filter by project



status - Filter by status (pending/in\_progress/completed)



priority - Filter by priority (low/medium/high)



Response: 200 OK



json

\[

&#x20; {

&#x20;   "id": 2,

&#x20;   "title": "Test Task from API",

&#x20;   "description": "",

&#x20;   "status": "pending",

&#x20;   "priority": "medium",

&#x20;   "project": 26,

&#x20;   "project\_name": "Test Project",

&#x20;   "due\_date": null,

&#x20;   "created\_at": "2026-04-29T02:48:57Z"

&#x20; }

]

Create Task

http

POST /api/projects/tasks/

Request Body:



json

{

&#x20; "project": 26,

&#x20; "title": "Complete documentation",

&#x20; "description": "Write API docs",

&#x20; "priority": "high",

&#x20; "status": "pending",

&#x20; "due\_date": "2026-05-15T00:00:00Z",

&#x20; "assigned\_to": 2

}

Update Task

http

PUT /api/projects/tasks/{id}/

json

{

&#x20; "status": "completed",

&#x20; "completed\_at": "2026-04-30T10:00:00Z"

}

Delete Task

http

DELETE /api/projects/tasks/{id}/

5\. Comments Endpoints

Get Comments

http

GET /api/comments/?project\_id=26

Response: 200 OK



json

\[

&#x20; {

&#x20;   "id": 1,

&#x20;   "content": "This project is awesome!",

&#x20;   "user\_email": "admin@gmail.com",

&#x20;   "created\_at": "2026-04-29T00:35:38Z",

&#x20;   "project": 26

&#x20; }

]

Create Comment

http

POST /api/comments/

Request Body:



json

{

&#x20; "project": 26,

&#x20; "content": "Great progress!"

}

6\. Dashboard Endpoints

Dashboard Stats

http

GET /api/projects/dashboard/stats/

Response: 200 OK



json

{

&#x20; "organization\_name": "Acme Inc",

&#x20; "organization\_plan": "trial",

&#x20; "total\_projects": 8,

&#x20; "total\_tasks": 2,

&#x20; "completed\_tasks": 0,

&#x20; "pending\_tasks": 2,

&#x20; "in\_progress\_tasks": 0,

&#x20; "total\_users": 1,

&#x20; "user\_role": "member",

&#x20; "is\_owner": true

}

Real-time Dashboard

http

GET /api/dashboard/realtime/

Response: 200 OK



json

{

&#x20; "project\_trends": \[

&#x20;   {"date": "2026-04-29", "count": 3},

&#x20;   {"date": "2026-04-28", "count": 5}

&#x20; ],

&#x20; "completion\_rate": 0.0,

&#x20; "active\_users": 1,

&#x20; "total\_projects": 8,

&#x20; "total\_tasks": 2,

&#x20; "total\_comments": 4

}

7\. Search Endpoints

Global Search

http

GET /api/search/global/?q=project

Response: 200 OK



json

{

&#x20; "query": "project",

&#x20; "total\_results": 9,

&#x20; "results": {

&#x20;   "projects": \[...],

&#x20;   "tasks": \[...],

&#x20;   "comments": \[...]

&#x20; }

}

8\. Export Endpoints

Export Projects to CSV

http

GET /api/projects/export/projects/csv/

Response: CSV file download



Export Tasks to CSV

http

GET /api/projects/export/tasks/csv/

Export Projects to PDF

http

GET /api/projects/export/projects/pdf/

Export Projects to Excel

http

GET /api/projects/export/projects/excel/

9\. Health Check

http

GET /health/

Response: 200 OK



json

{

&#x20; "status": "healthy",

&#x20; "timestamp": "2026-04-30T10:00:00Z",

&#x20; "checks": {

&#x20;   "database": "up",

&#x20;   "cache": "up"

&#x20; }

}

10\. Activity Feed

http

GET /api/activity-feed/

Response: 200 OK



json

{

&#x20; "total": 14,

&#x20; "activities": \[

&#x20;   {

&#x20;     "type": "project\_created",

&#x20;     "title": "Project \\"Test Project\\" was created",

&#x20;     "user": "admin@gmail.com",

&#x20;     "timestamp": "2026-04-29T00:04:34Z",

&#x20;     "project\_id": 26

&#x20;   }

&#x20; ]

}

11\. AI Suggestions

http

GET /api/ai/suggestions/26/

Response: 200 OK



json

{

&#x20; "project\_id": 26,

&#x20; "suggestions": \[

&#x20;   {

&#x20;     "title": "Complete Test Project documentation",

&#x20;     "description": "Document all features",

&#x20;     "priority": "medium",

&#x20;     "similarity\_score": 0.5

&#x20;   }

&#x20; ]

}

Error Codes

Code	Meaning

200	Success

201	Created

204	No Content

400	Bad Request

401	Unauthorized

403	Forbidden

404	Not Found

500	Server Error

Rate Limiting

Anonymous: 100 requests/day



Authenticated: 1000 requests/day



Burst: 60 requests/minute



Swagger Documentation

Interactive API docs available at:



text

http://localhost:8000/swagger/

http://localhost:8000/redoc/



