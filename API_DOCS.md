
---

# 📡 3. CLEAN API.md

```markdown
# 📡 Multi-Tenant SaaS API Documentation

## Base URL
http://localhost:8000/api

---

## 🔐 Authentication

### Register
POST /auth/register/

```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "organization_name": "My Company"
}

Login

POST /auth/login/

{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response:

{
  "access": "jwt_token",
  "refresh": "jwt_token"
}
🏢 Organizations
Get Organization

GET /organizations/

Update Organization

PUT /organizations/

📁 Projects
List Projects

GET /projects/

Supports:

pagination
filtering
search
Create Project

POST /projects/

{
  "name": "Project Alpha",
  "description": "Example project"
}
Update Project

PATCH /projects/{id}/

Delete Project

DELETE /projects/{id}/

✅ Tasks
Create Task

POST /projects/tasks/

{
  "project": 1,
  "title": "New Task",
  "priority": "high"
}
Update Task

PATCH /projects/tasks/{id}/

💬 Comments
Add Comment

POST /comments/

{
  "project": 1,
  "content": "Great work"
}
🔔 Notifications
Get Notifications

GET /notifications/

📊 Dashboard
Stats

GET /projects/dashboard/stats/

🔍 Search

GET /search/global/?q=keyword

⚡ WebSockets
Notifications

ws://localhost:8001/ws/notifications/

❌ Errors
{
  "error": "message"
}
🔐 Rate Limiting

Applied on:

auth endpoints
create/update endpoints
search endpoints
📌 Summary

This API provides:

Multi-tenant secure access
Clean REST design
Pagination & filtering
Real-time updates
Scalable backend structure