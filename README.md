# Multi-Tenant SaaS Platform — Backend API
![Stripe](https://img.shields.io/badge/Stripe-test%20mode-635bff?logo=stripe&logoColor=white)
![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-499%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Celery](https://img.shields.io/badge/Celery-enabled-green)
![Docker](https://img.shields.io/badge/Docker-enabled-blue)


## Multi-Tenant SaaS Platform

>A scalable SaaS backend that enables multiple organizations to use the same application securely with complete data isolation. Built with Django REST Framework, it implements tenant-aware architecture, role-based permissions, JWT authentication, and production-ready API design patterns.


## 🌐 Live Demo

| | URL |
|--|--|
| **API Base** | https://saas-app-zrq8.onrender.com |
| **Swagger Docs** | https://saas-app-zrq8.onrender.com/api/docs/ |
| **ReDoc** | https://saas-app-zrq8.onrender.com/api/redoc/ |
| **Health Check** | https://saas-app-zrq8.onrender.com/health/ |

> ⚠️ Hosted on Render free tier — first request may take 50 seconds to wake up.

## 📊 Quality Metrics

- 499 automated tests
- 87% code coverage
- Multi-tenant isolation tests included
- Integration + unit + permission test layers

A Django REST Framework backend that demonstrates multi-tenant SaaS architecture, tenant isolation, JWT authentication, real-time communication, background processing, and production-oriented deployment practices using Docker, Nginx, Redis, and Celery.
---

## 📸 API Documentation Preview

> Full interactive documentation available at `/api/docs/` — supports JWT authentication directly in the browser.

### Overview & Authentication
![Swagger Overview](docs/swagger1.png)

### Projects & Tasks
![Projects and Tasks](docs/swagger2.png)

### Organizations & Notifications
![Organizations and Notifications](docs/swagger3.png)


---

## 🚀 Key Highlights

- Multi-tenant architecture with organization-level row-level data isolation
- JWT authentication with access/refresh tokens, email verification, and password reset
- Role-based access control — Admin, Member, Viewer
- Project and task management with search, filtering, bulk operations, and exports
- Real-time notifications via Django Channels and WebSockets
- Background task processing with Celery and Redis
- Redis caching for dashboard stats, project lists, and search results
- Nginx reverse proxy with Gunicorn (HTTP) and Daphne (WebSocket)
- 499 automated tests with 87% code coverage across unit, integration, and permission tests

---

## 🛠 Tech Stack

| Layer            | Technology                    |
| ---------------- | ----------------------------- |
| Backend          | Django 5.2, Django REST Framework |
| Database         | PostgreSQL 16                 |
| Cache & Broker   | Redis 7                       |
| Background Tasks | Celery + django-celery-beat   |
| Real-Time        | Django Channels + Daphne      |
| Authentication   | JWT via SimpleJWT             |
| API Docs         | drf-spectacular (Swagger/OpenAPI 3.0) |
| Testing          | Pytest + pytest-django        |
| Containerization | Docker + Docker Compose       |
| Reverse Proxy    | Nginx                         |



## 📁 Project Structure

```
multi-tenant-saas/
├── accounts/            # Auth, registration, email verification, password reset
├── organizations/       # Tenant management, invitations, middleware
├── projects/            # Project CRUD, search, bulk operations, exports
├── notifications/       # Real-time notifications via WebSockets
├── billing/             # Plan management, subscription tracking
├── webhooks/            # Configurable outbound webhooks
└── core/                # Settings, URLs, middleware, pagination
```
---

## 🏢 Multi-Tenancy Architecture

This platform uses a **shared database with row-level tenant isolation** — every model is scoped to an `organization_id`, and every queryset is filtered through Django middleware that identifies the tenant from the authenticated user's JWT token.

### Why shared database?

- Lower infrastructure cost vs. schema-per-tenant or database-per-tenant
- Simpler migrations and deployment
- Scales well for small to mid-size SaaS products
- Easier tenant onboarding

### Trade-offs managed:

- Strict query-level filtering enforced via `TenantMiddleware`
- Comprehensive isolation tests verify cross-tenant data leakage is impossible
- Role-based permissions add a second layer of access control within each tenant

---

## 🔐 Authentication & Authorization

### Authentication Flow
- Register with organization name → creates user + organization in one step
- JWT access token (15 min) + refresh token (7 days) with rotation and blacklisting
- Email verification required before full access
- Password reset via secure token sent to email

### Role-Based Access Control

| Role   | Projects | Tasks | Users | Admin |
|--------|----------|-------|-------|-------|
| Admin  | Full     | Full  | Full  | Yes   |
| Member | Own only | Own/Assigned | No | No |
| Viewer | Read     | Assigned | No | No |

---
## 📁  Core Modules

### Projects
- CRUD, search, filtering
- Bulk archive/delete
- CSV/PDF/Excel export

### Tasks
- Assignment and status tracking
- Subtasks and dependencies
- Bulk updates

### Notifications
- Real-time WebSocket notifications
- Read/unread management

### Billing
- Stripe Checkout
- Subscription management
- Webhook synchronization

> ⚠️ Currently configured for Stripe **test mode** only — live payments are pending regional availability. Switching to production is a matter of swapping test API keys for live keys; no code changes required.

### Additional Modules
- **Webhooks** — configurable outbound webhooks per organization
- **Custom Fields** — dynamic fields on projects per organization
- **Time Tracking** — log hours per task
- **Search** — global search across projects and tasks
- **Chat** — organization-scoped messaging

---

## 📡 API Endpoints

| Resource | Base Endpoint |
|----------|---------------|
| Authentication | `/api/auth/*` |
| Organizations | `/api/organizations/*` |
| Projects | `/api/projects/*` |
| Tasks | `/api/projects/tasks/*` |
| Notifications | `/api/notifications/*` |
| Billing | `/api/billing/*` |
| Webhooks | `/api/webhooks/*` |

> 📖 Full interactive API documentation (Swagger/OpenAPI) is available at **`/api/docs/`**.

---

## 💡 Example API Usage

**Register and get JWT token:**
```bash
curl -X POST http://localhost:8080/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mycompany.com",
    "password": "securepass123",
    "password2": "securepass123",
    "first_name": "Andualem",
    "last_name": "Getachew",
    "organization_name": "My Company"
  }'
```

**Create a project:**
```bash
curl -X POST http://localhost:8080/api/projects/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend API", "description": "Our main API project"}'
```

**Create a task:**
```bash
curl -X POST http://localhost:8080/api/projects/tasks/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Set up CI/CD", "project": 1, "priority": "high"}'
```

---

## ⚡ Performance Strategy

Caching
Database Optimization
API Optimization

---

## 🔌 Real-Time Architecture

flowchart TD
    Client --> Nginx
    Nginx --> Gunicorn
    Nginx --> Daphne
    Gunicorn --> PostgreSQL
    Gunicorn --> Redis
    Redis --> Celery

---

## ⚙️ Background Tasks (Celery)

Scheduled and async tasks handled by Celery workers with Redis as the broker:

- Email sending (verification, password reset, notifications)
- Audit log processing
- Report and export generation
- Cache warming on startup
- Periodic cleanup tasks via django-celery-beat

---

## 🔐 Security

- JWT with short-lived access tokens (15 min) and refresh rotation
- Organization-level data isolation at query level
- Role-based permissions enforced on every view
- Rate limiting on auth endpoints (5/min login, 3/min register)
- CORS protection with configurable allowed origins
- Input validation via DRF serializers
- SQL injection prevention via Django ORM

---

## 🏗 System Architecture

Client (Web / Mobile)
↓
Nginx (port 8080)
├── /ws/  → Daphne (WebSockets, port 8001)
└── /     → Gunicorn (HTTP, port 8000)
↓
Django REST API + Django Channels
↓
PostgreSQL          Redis
(Tenant Data)   (Cache + Broker)
↓
Celery Workers
Celery Beat (Scheduler)

---

## 🧪 Testing

```bash
# Run full test suite inside Docker
docker-compose exec web pytest --tb=short -q

# With coverage report
docker-compose exec web pytest --cov=. --cov-report=term-missing
```

### Test Coverage: 87% (147 tests)

499 automated tests

### Test Coverage

- 499  automated tests
- 87% code coverage
- Authentication
- Tenant isolation
- Permissions
- Project & Task APIs
- Billing
- Edge cases

....

---

## 📦 Local Setup

```bash
git clone https://github.com/andugetachew/multi-tenant-saas.git
cd multi-tenant-saas

# Copy environment file
cp .env.example .env
# Fill in your values in .env

# Start all services
docker-compose up --build
```

Access points:
- API: `http://localhost:8080/`
- Swagger Docs: `http://localhost:8080/api/docs/`
- Admin Panel: `http://localhost:8080/admin/`

---

## 🔑 Environment Variables

```env
DATABASE_URL=
REDIS_URL=
SECRET_KEY=

STRIPE_SECRET_KEY=
EMAIL_HOST_USER=

...

```

---

## 🐳 Docker Services

```bash
docker-compose up --build
```

| Service     | Purpose       |
| ----------- | ------------- |
| web         | Django API    |
| daphne      | WebSockets    |
| nginx       | Reverse Proxy |
| postgres    | Database      |
| redis       | Cache/Broker  |
| celery      | Worker        |
| celery-beat | Scheduler     |


---

## 🎯 Design Decisions

### Shared Database Multi-Tenancy
Chose shared database with row-level isolation over schema-per-tenant because it reduces operational complexity, simplifies migrations, and scales well for early-stage SaaS. The trade-off is stricter query discipline, addressed through middleware and comprehensive isolation tests.

### Django Channels + Daphne
Separated WebSocket handling (Daphne/ASGI) from HTTP handling (Gunicorn/WSGI) behind Nginx for clean separation of concerns and independent scaling.

### Redis for Both Cache and Broker
Single Redis instance serves both Celery task queue and Django cache layer, reducing infrastructure complexity while keeping both concerns functionally separate through database index separation.

### pytest over Django TestCase
Chose pytest for cleaner fixture management, better parametrize support, and more readable assertions — especially important for multi-tenant isolation tests that require complex setup.

### Dual Billing Path: Stripe Checkout + Manual Approval
Rather than routing every plan change through Stripe, the platform keeps two paths that share a single sync mechanism. Self-serve plans (Basic, Pro) go through Stripe Checkout for instant, unattended activation — the expected UX for standard SaaS pricing tiers. A manual request-and-approve flow remains available for cases that don't fit a fixed self-serve price (negotiated terms, non-Stripe regions, admin-granted upgrades). Both paths call the same sync helper after activation, keeping `Organization` and `Subscription` state consistent regardless of which path was used.

### Webhook Idempotency
Stripe explicitly documents that webhook events can be delivered more than once for the same event ID (network retries, timeouts). Incoming events are checked against a processed-events table before handling — duplicate deliveries are acknowledged but skipped, preventing double-recorded transactions or repeated state changes.
---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Andualem Getachew**

[![GitHub](https://img.shields.io/badge/GitHub-andugetachew-black?logo=github)](https://github.com/andugetachew)
[![Email](https://img.shields.io/badge/Email-andugeta41%40gmail.com-red?logo=gmail)](mailto:andugeta41@gmail.com)