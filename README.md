# Multi-Tenant SaaS Platform — Backend API
![Stripe](https://img.shields.io/badge/Stripe-test%20mode-635bff?logo=stripe&logoColor=white)
![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-147%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Celery](https://img.shields.io/badge/Celery-enabled-green)
![Docker](https://img.shields.io/badge/Docker-enabled-blue)

## 🌐 Live Demo

| | URL |
|--|--|
| **API Base** | https://saas-app-zrq8.onrender.com |
| **Swagger Docs** | https://saas-app-zrq8.onrender.com/api/docs/ |
| **ReDoc** | https://saas-app-zrq8.onrender.com/api/redoc/ |
| **Health Check** | https://saas-app-zrq8.onrender.com/health/ |

> ⚠️ Hosted on Render free tier — first request may take 50 seconds to wake up.

## 📊 Quality Metrics

- 147 automated tests
- 87% code coverage
- Multi-tenant isolation tests included
- Integration + unit + permission test layers

A production-grade SaaS backend built with Django REST Framework that supports multi-tenancy, JWT authentication, project and task management, real-time notifications, background processing, and scalable architecture patterns.

Built to demonstrate real-world backend engineering skills including multi-tenancy, scalable architecture design, asynchronous processing, and production deployment patterns used in SaaS systems.

Designed to demonstrate backend engineering best practices including tenant isolation, asynchronous task processing, Redis caching, comprehensive testing, and containerized deployment with Nginx.

---

## 📸 API Documentation Preview

> Full interactive documentation available at `/api/docs/` — supports JWT authentication directly in the browser.

### Overview & Authentication
![Swagger Overview](docs/swagger1.png)

### Projects & Tasks
![Projects and Tasks](docs/swagger2.png)

### Organizations & Notifications
![Organizations and Notifications](docs/swagger3.png)

### Analytics, Billing & More
![Analytics and Billing](docs/swagger4.png)

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
- 147 automated tests with 87% code coverage across unit, integration, and permission tests

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
│   ├── views.py         # ProjectListCreateView, TaskListCreateView, analytics
│   ├── bulk_ops.py      # BulkProjectDeleteView, BulkTaskUpdateView
│   ├── export_views.py  # CSV, PDF, Excel exports
│   └── search.py        # ProjectSearch, TaskSearch
├── notifications/       # Real-time notifications via WebSockets
├── audit/               # Activity logging middleware
├── billing/             # Plan management, subscription tracking
├── analytics/           # Dashboard analytics, revenue metrics
├── tracking/            # Time tracking per task
├── chat/                # Organization-scoped messaging
├── webhooks/            # Configurable outbound webhooks
├── custom_fields/       # Dynamic fields per organization
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

## 📁 Core Modules

### Projects
- Full CRUD with organization-scoped queries
- Search and filtering by status, date, tags
- CSV, PDF, and Excel export
- Bulk archive and bulk delete
- Project templates

### Tasks
- Task assignment to organization members
- Status tracking: pending → in_progress → completed
- Priority levels: low, medium, high
- Subtasks and task dependencies
- Bulk status updates
- Time tracking entries per task

### Comments
- Nested threaded comments on projects and tasks
- Real-time delivery via WebSockets

### Notifications
- In-app notifications with read/unread state
- Real-time push via Django Channels
- Mark all read, delete individual

### Audit Logs
- Every create/update/delete action logged with user, IP, timestamp
- Organization-scoped activity feed
- Cursor-paginated for infinite scroll

### Analytics & Reports
- Dashboard stats: total projects, tasks by status, user counts
- Revenue analytics, seller performance (multi-tenant metrics)
- Comprehensive report generation
- Real-time dashboard with Redis-cached data

### Billing
- Plan management (Free, Basic, Pro) with per-plan feature limits and Stripe price mapping
- **Stripe Checkout integration** — self-serve subscription upgrades via Stripe-hosted checkout (test mode)
- **Webhook-driven activation** — subscriptions, invoices, and organization plan state sync automatically on payment events (`checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted`)
- **Idempotent webhook processing** — duplicate Stripe events (a documented Stripe behavior) are detected and skipped, preventing double-charged transaction records
- Manual upgrade request + admin approval workflow, kept in sync with the Stripe path via a shared subscription-sync helper
- Self-serve cancellation (cancel at end of billing period, preserving paid-for access)
- 24 dedicated tests covering checkout, webhook processing, upgrade requests, admin approval, and cancellation (mocked Stripe API — no real API calls in test suite)

> ⚠️ Currently configured for Stripe **test mode** only — live payments are pending regional availability. Switching to production is a matter of swapping test API keys for live keys; no code changes required.

### Additional Modules
- **Webhooks** — configurable outbound webhooks per organization
- **Custom Fields** — dynamic fields on projects per organization
- **Time Tracking** — log hours per task
- **Search** — global search across projects and tasks
- **Chat** — organization-scoped messaging

---

## 📡 API Endpoints

| Module         | Endpoint                          | Methods         |
| -------------- | --------------------------------- | --------------- |
| Auth           | `/api/auth/register/`             | POST            |
| Auth           | `/api/auth/login/`                | POST            |
| Auth           | `/api/auth/token/refresh/`        | POST            |
| Auth           | `/api/auth/profile/`              | GET, PUT, PATCH |
| Auth           | `/api/auth/verify-email/`         | POST            |
| Auth           | `/api/auth/forgot-password/`      | POST            |
| Organizations  | `/api/organizations/`             | GET, PUT, PATCH |
| Organizations  | `/api/organizations/invite/`      | POST            |
| Projects       | `/api/projects/`                  | GET, POST       |
| Projects       | `/api/projects/<id>/`             | GET, PUT, PATCH, DELETE |
| Projects       | `/api/projects/search/`           | GET             |
| Projects       | `/api/projects/bulk-delete/`      | POST            |
| Projects       | `/api/projects/bulk-archive/`     | POST            |
| Projects       | `/api/projects/dashboard/stats/`  | GET             |
| Projects       | `/api/projects/export/projects/csv/` | GET          |
| Tasks          | `/api/projects/tasks/`            | GET, POST       |
| Tasks          | `/api/projects/tasks/<id>/`       | GET, PUT, PATCH, DELETE |
| Tasks          | `/api/projects/tasks/search/`     | GET             |
| Tasks          | `/api/projects/tasks/bulk-update/`| POST            |
| Notifications  | `/api/notifications/`             | GET             |
| Notifications  | `/api/notifications/mark-all-read/` | POST          |
| Analytics      | `/api/analytics/dashboard/`       | GET             |
| Audit          | `/api/audit/`                     | GET             |
| Search         | `/api/search/global/`             | GET             |
| Billing        | `/api/billing/plans/`             | GET             |
| Webhooks       | `/api/webhooks/`                  | GET, POST       |
| Billing        | `/api/billing/plans/`             | GET             |
| Billing        | `/api/billing/subscription/`      | GET             |
| Billing        | `/api/billing/checkout/`          | POST            |
| Billing        | `/api/billing/upgrade/request/`   | POST            |
| Billing        | `/api/billing/cancel/`            | POST            |
| Billing        | `/api/billing/webhook/stripe/`    | POST            |
Full interactive documentation: `/api/docs/`

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

### Redis Caching
- Dashboard statistics — 5 min TTL
- Real-time dashboard — 3 min TTL
- Project list — 2 min TTL
- Search results — 1 min TTL

### Database Optimization
- Indexes on `organization_id`, `created_at`, and all foreign keys
- `select_related()` for ForeignKey traversals
- `prefetch_related()` for reverse relations
- `defer()` for large text fields not needed in list views

### API Performance
- Pagination on all list endpoints (20 per page default)
- Cursor pagination for activity feeds (infinite scroll)
- Query count optimization in serializers

---

## 🔌 Real-Time Architecture

Client WebSocket
↓
Nginx (/ws/ route)
↓
Daphne (ASGI server, port 8001)
↓
Django Channels
↓
Redis Channel Layer

Supported events: task updates, new notifications, user activity

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

| Test Category              | Status |
|---------------------------|--------|
| Authentication & JWT       | ✅ 27 tests |
| Email Verification         | ✅ 4 tests  |
| Organization Management    | ✅ 15 tests |
| Multi-Tenant Isolation     | ✅ 6 tests  |
| Project API                | ✅ 29 tests |
| Task API                   | ✅ 14 tests |
| Permission & Role Tests    | ✅ 19 tests |
| Integration Workflows      | ✅ 3 tests  |
| Export Tests               | ✅ 2 tests  |
| Edge Cases                 | ✅ 23 tests |

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
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=multitenant_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=yourpassword
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

FRONTEND_URL=http://localhost:3000
```

---

## 🐳 Docker Services

```bash
docker-compose up --build
```

| Service      | Description                        | Port  |
|--------------|------------------------------------|-------|
| web          | Django + Gunicorn (HTTP)           | 8000  |
| daphne       | Django Channels (WebSocket)        | 8001  |
| nginx        | Reverse proxy                      | 8080  |
| db           | PostgreSQL 16                      | 5434  |
| redis        | Cache + Message broker             | 6381  |
| celery       | Background task worker             | —     |
| celery-beat  | Periodic task scheduler            | —     |

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