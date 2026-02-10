# System Integration Roadmap - Updated with JWT Auth

## Project Overview
Sistema de onboarding SaaS automatizado con:
- ✅ Registro de clientes (Fase 1)
- ✅ Integración Stripe (Fase 1)
- ✅ Dashboard administrativo (Fase 1)
- ✅ **Autenticación JWT** (Fase 1 - NEW)
- ⏳ Integración de templates avanzados (Fase 2)
- ⏳ Gestión de tenants CRUD (Fase 2)
- ⏳ Sistema de logs real-time (Fase 3)

## Phase 1: MVP Admin Dashboard + JWT Auth ✅ COMPLETE

### Completed Components
- ✅ Admin dashboard UI (Tailwind CSS, Material Icons)
- ✅ Real-time metrics from PostgreSQL (revenue, active tenants, pending)
- ✅ Dynamic tenant list with status badges
- ✅ JWT authentication system
- ✅ Login page with credential entry
- ✅ Token generation and validation
- ✅ Protected API endpoints
- ✅ Client-side token management
- ✅ Logout functionality

### Key Files
- `templates/admin_dashboard.html` (390+ lines) - Interactive dashboard
- `templates/admin_login.html` (268 lines) - Login page
- `app/main.py` (446 lines) - Backend with JWT + API endpoints
- `docs/JWT_AUTHENTICATION.md` - Complete JWT reference
- `docs/JWT_QUICKSTART.md` - Quick start guide
- `test_jwt.sh` - Automated test script

### Testing Status
✅ Login endpoint returns valid JWT token
✅ Protected endpoints respond with metrics data
✅ Token validation working correctly
✅ Login page renders successfully
✅ Database queries return correct data

### Environment Setup
```bash
# Activate environment
source /opt/onboarding-system/venv/bin/activate

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload

# Access
- Login: http://localhost:4443/login
- Dashboard: http://localhost:4443/admin
- API Docs: http://localhost:4443/docs
```

---

## Phase 2: Advanced Admin Templates + CRUD Operations ⏳ PLANNED

### 2.1 Billing & Payment History Template
**Endpoint**: `GET /admin/billing`

**Database Requirements**:
- Query: Join `customers` + `subscriptions` + `stripe_events`
- Show: Invoice history, payment failures, refunds
- Data needed: `stripe_invoice_id`, `amount_paid`, `payment_date`

**API Endpoints**:
```
GET /api/billing/invoices - List all invoices
GET /api/billing/invoices/{id} - Invoice details
GET /api/billing/payment-failures - Recent failures
POST /api/billing/retry-payment - Retry failed payment
```

**Template Features**:
- Invoice table with sorting/filtering
- Payment method management
- Refund history
- PDF export functionality
- Charts showing payment trends

### 2.2 Advanced Reports & PDF Export Template
**Endpoint**: `GET /admin/reports`

**Database Requirements**:
- Query: Aggregated metrics (revenue, churn, growth)
- Time ranges: Daily, weekly, monthly, custom
- Data needed: Subscription status changes, tenant metrics

**API Endpoints**:
```
GET /api/reports/revenue - Revenue analytics
GET /api/reports/churn - Churn analysis
GET /api/reports/growth - Growth metrics
GET /api/reports/export?format=pdf - Export as PDF
```

**Template Features**:
- Revenue dashboards (MRR, ARR, growth rate)
- Churn analysis with predictions
- Tenant segmentation by plan
- PDF/CSV export with html2pdf.js
- Interactive charts with Chart.js

### 2.3 System Management & Logs Template
**Endpoint**: `GET /admin/logs`

**Database Requirements**:
- New table: `system_logs` (timestamp, level, message, source)
- WebSocket for real-time updates
- Data needed: Provisioning logs, error logs, audit trail

**API Endpoints**:
```
GET /api/logs - List system logs (with pagination)
GET /api/logs/stream - WebSocket endpoint for live logs
GET /api/logs/export - Export logs as CSV
POST /api/logs/search - Search logs with filters
```

**Template Features**:
- Log viewer with filtering (level, date, source)
- Real-time log streaming via WebSocket
- Export to CSV functionality
- Error highlighting and navigation
- Search and advanced filtering

### 2.4 Tenant Configuration & Maintenance Template
**Endpoint**: `GET /admin/tenants/{id}/config`

**API Endpoints for CRUD**:
```
PATCH /api/tenants/{id} - Update tenant config
  - Fields: subdomain, plan, max_users, storage_limit, resource_limits
  - Response: Updated tenant object

DELETE /api/tenants/{id} - Suspend/delete tenant
  - Query param: ?action=suspend|delete
  - Response: Confirmation message

GET /api/tenants/{id}/health - Tenant health check
  - Response: {"status", "uptime", "resource_usage"}
```

**Template Features**:
- Subdomain management and availability check
- Plan upgrade/downgrade
- Resource limit configuration
- Maintenance mode toggle
- Database backup management

### 2.5 Customer & Advanced Tenant Management Template
**Endpoint**: `GET /admin/customers`

**API Endpoints**:
```
GET /api/customers - List all customers with subscriptions
GET /api/customers/{id} - Customer details
PATCH /api/customers/{id} - Update customer info
GET /api/customers/{id}/activity - Customer activity log
POST /api/customers/{id}/action - Perform action (suspend, reactivate)
```

**Template Features**:
- Advanced customer search and filtering
- Customer activity timeline
- Batch actions (suspend multiple, send message)
- Customer segment management
- Risk scoring (churn prediction)

### 2.6 Advanced System Admin Console Template
**Endpoint**: `GET /admin/system`

**API Endpoints**:
```
GET /api/system/stats - Overall system statistics
GET /api/system/resources - Resource usage (CPU, RAM, Disk)
POST /api/system/admin-action - Execute admin commands
  - Actions: restart-service, clear-cache, trigger-backup
GET /api/system/database - Database health and stats
```

**Template Features**:
- System health dashboard
- Resource monitoring (real-time graphs)
- Dangerous admin actions with confirmation
- Service restart/restart management
- Database optimization tools

---

## Phase 3: Real-time Monitoring & Advanced Features ⏳ PLANNED

### 3.1 WebSocket Log Streaming
```
Connection: ws://localhost:4443/ws/logs
Message format: {"timestamp", "level", "message", "source"}
Auto-reconnect on disconnect
```

### 3.2 Monitoring & Alerting
- Real-time CPU/RAM/Disk monitoring
- Alert thresholds configuration
- Email/Slack notifications
- Historical metrics storage

### 3.3 Analytics Enhancement
- Real-time analytics dashboard
- Heatmaps for user activity
- Conversion funnel tracking
- Cohort analysis

---

## Database Schema Enhancements

### Current Tables
```
✅ customers
✅ subscriptions
✅ stripe_events
```

### Planned Tables (Phase 2-3)
```
⏳ system_logs (id, timestamp, level, message, source)
⏳ billing_invoices (id, customer_id, amount, status, date)
⏳ audit_logs (id, admin_id, action, target, timestamp)
⏳ tenant_health (id, tenant_id, cpu, ram, disk, timestamp)
⏳ payment_methods (id, customer_id, stripe_pm_id, type, default)
```

---

## API Endpoint Summary

### Phase 1 ✅
| Method | Endpoint | Protected | Status |
|--------|----------|-----------|--------|
| GET | `/` | ❌ | ✅ |
| POST | `/api/checkout` | ❌ | ✅ |
| POST | `/webhook/stripe` | ⚠️ | ✅ |
| GET | `/admin` | ✅ | ✅ |
| GET | `/login` | ❌ | ✅ |
| POST | `/api/admin/login` | ❌ | ✅ |
| GET | `/api/dashboard/metrics` | ✅ | ✅ |
| GET | `/api/tenants` | ✅ | ✅ |
| POST | `/api/tenants` | ✅ | ⚠️ (stub) |

### Phase 2 ⏳
| Method | Endpoint | Protected | Status |
|--------|----------|-----------|--------|
| GET | `/admin/billing` | ✅ | ⏳ |
| GET | `/api/billing/invoices` | ✅ | ⏳ |
| GET | `/admin/reports` | ✅ | ⏳ |
| GET | `/api/reports/revenue` | ✅ | ⏳ |
| PATCH | `/api/tenants/{id}` | ✅ | ⏳ |
| DELETE | `/api/tenants/{id}` | ✅ | ⏳ |
| GET | `/admin/logs` | ✅ | ⏳ |
| GET | `/api/logs` | ✅ | ⏳ |
| GET | `/admin/customers` | ✅ | ⏳ |
| GET | `/admin/system` | ✅ | ⏳ |

### Phase 3 ⏳
| Protocol | Endpoint | Protected | Status |
|----------|----------|-----------|--------|
| WS | `/ws/logs` | ✅ | ⏳ |
| WS | `/ws/metrics` | ✅ | ⏳ |

---

## Technology Stack

### Backend
- FastAPI 0.115.0
- SQLAlchemy 2.0.35
- PostgreSQL
- PyJWT (JWT authentication)
- Stripe API
- Pydantic 2.9.0

### Frontend
- HTML5 + CSS3
- Tailwind CSS 3
- Material Design Icons
- Vanilla JavaScript (no framework)
- Chart.js (analytics charts)
- html2pdf.js (PDF export)

### Infrastructure
- Uvicorn ASGI server
- LXC containers (Odoo provisioning)
- Docker (future)
- CI/CD (planned)

---

## Security Checklist

### Phase 1 ✅
- ✅ HTTPS ready (port 4443)
- ✅ JWT authentication
- ✅ HMAC-SHA256 token signing
- ✅ Token expiration
- ✅ Protected routes

### Phase 2 ⏳
- ⏳ 2FA implementation
- ⏳ Rate limiting
- ⏳ Audit logging
- ⏳ RBAC (role-based access)
- ⏳ API key management

### Phase 3 ⏳
- ⏳ SOC 2 compliance
- ⏳ Data encryption at rest
- ⏳ Advanced threat detection
- ⏳ Incident response procedures

---

## Development Timeline

### Phase 1: MVP + JWT ✅ COMPLETE
- Duration: ~1 week
- Status: Ready for production
- Tests: All passing

### Phase 2: Advanced Features ⏳ 2-3 weeks
- Billing template integration
- Reports template integration
- Logs template integration
- CRUD operations
- PDF export

### Phase 3: Real-time & Monitoring ⏳ 1-2 weeks
- WebSocket streaming
- Real-time metrics
- Alerting system
- Advanced analytics

---

## Known Limitations & TODOs

### Current Limitations
- 🔴 CPU/RAM metrics are placeholder (needs Prometheus or psutil)
- 🔴 Stripe webhook not fully integrated with tenant provisioning
- 🔴 No email notifications yet
- 🔴 No 2FA implemented
- 🔴 localStorage used for token (XSS vulnerable - use httpOnly cookie in prod)

### Immediate TODOs
- [ ] Add rate limiting to login endpoint
- [ ] Implement refresh tokens
- [ ] Add audit logging for admin actions
- [ ] Implement RBAC
- [ ] Add 2FA

### Future Enhancements
- [ ] Mobile app
- [ ] API v2 with GraphQL
- [ ] AI-powered recommendations
- [ ] Advanced analytics

---

## Testing & Quality

### Test Coverage
- ✅ Unit tests for JWT functions
- ✅ Integration tests for login flow
- ✅ API endpoint tests
- ⏳ E2E tests (Selenium/Cypress)
- ⏳ Performance tests
- ⏳ Security tests

### Automated Tests
```bash
bash /opt/onboarding-system/test_jwt.sh
```

### Manual Testing Checklist
- [ ] Login with correct credentials
- [ ] Login with incorrect credentials
- [ ] Access dashboard without token
- [ ] Token expiration after 24 hours
- [ ] Logout clears token
- [ ] All API endpoints return correct data

---

## Documentation

### Available Docs
- ✅ `docs/JWT_AUTHENTICATION.md` - Complete JWT reference
- ✅ `docs/JWT_QUICKSTART.md` - Quick start guide
- ✅ `docs/JWT_IMPLEMENTATION_SUMMARY.md` - Implementation details
- ✅ `docs/ADMIN_DASHBOARD.md` - Dashboard API docs
- ✅ `docs/INTEGRATION_SUMMARY.md` - Overall integration guide
- ✅ `.github/copilot-instructions.md` - AI agent guidance

### Documentation TODOs
- [ ] Postman collection for all endpoints
- [ ] OpenAPI/Swagger specification
- [ ] Architecture decision records (ADRs)
- [ ] Deployment guide
- [ ] Troubleshooting guide

---

## Conclusion

The Onboarding System has successfully completed Phase 1 with:
- ✅ Functional admin dashboard
- ✅ Real-time metrics from PostgreSQL
- ✅ JWT authentication system
- ✅ Protected API endpoints
- ✅ Professional login UI
- ✅ Comprehensive documentation

**Status**: Ready for Phase 2 development and production deployment (after security hardening).

**Next Action**: Begin Phase 2 development - start with Billing template integration and CRUD operations.
