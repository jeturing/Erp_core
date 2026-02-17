# Blue-Green Deployment Runbook

**Sistema**: Sajet ERP Core (FastAPI + Svelte)  
**Ambiente**: Production  
**Estrategia**: Blue-Green con traffic shifting gradual  
**RTO**: 15 minutos | **RPO**: 5 minutos

---

## 📋 Pre-Deployment Checklist

**24 horas antes**:
- [ ] Todas las pruebas pasan (backend + frontend)
- [ ] Security scan aprobado
- [ ] Database migrations testeadas en staging
- [ ] Rollback plan documentado y validado
- [ ] Monitoring alerts configurados
- [ ] Team notificado (Slack, email)

**1 hora antes**:
- [ ] Todos los PRs merged a `main`
- [ ] Version number bumped (CHANGELOG.md)
- [ ] Docker images construidas y testeadas
- [ ] Staging deployment valida
- [ ] Database backups executed

---

## 🚀 Procedimiento de Deployment

### PASO 1: Crear Release Tag (5 min)

```bash
# En rama main, local
VERSION="v1.3.0"  # Usar semver
TAG_DATE=$(date +%Y-%m-%d_%H%M%S)

git tag -a ${VERSION} -m "Release ${VERSION} - Fase 3 Production

Release notes:
- 3 API gaps cerrados
- 66% reducción latencia dashboard
- 7 vulnerabilidades de seguridad corregidas
- Odoo 19 migration ready

Deployed by: [TU_NOMBRE]
Date: ${TAG_DATE}"

git push origin ${VERSION}
```

**Output esperado**:
```
Counting objects: 50, done.
Delta compression using up to 8 threads.
...
To github.com:jeturing/Erp_core.git
 * [new tag] v1.3.0 -> v1.3.0
```

### PASO 2: Build Docker Images (10 min)

```bash
# Backend
docker build \
  -f Dockerfile.backend \
  -t registry.sajet.us/erp-core-backend:${VERSION} \
  -t registry.sajet.us/erp-core-backend:latest \
  .

# Frontend
docker build \
  -f Dockerfile.frontend \
  -t registry.sajet.us/erp-core-frontend:${VERSION} \
  -t registry.sajet.us/erp-core-frontend:latest \
  frontend/

# Push a registry
docker push registry.sajet.us/erp-core-backend:${VERSION}
docker push registry.sajet.us/erp-core-frontend:${VERSION}
docker push registry.sajet.us/erp-core-backend:latest
docker push registry.sajet.us/erp-core-frontend:latest
```

**Validación**:
```bash
# Verificar images en registry
curl -s https://registry.sajet.us/v2/erp-core-backend/tags/list | jq
```

### PASO 3: Database Migrations (5 min)

```bash
# Conectar a PostgreSQL production
psql postgresql://jeturing:${DB_PASSWORD}@prod-db.sajet.us/erp_core_db

# Ejecutar migrations (asumiendo Alembic)
alembic upgrade head

# Verificar schema
SELECT version FROM alembic_version;
```

**Output esperado**:
```
 version     
─────────────
 abc123def456
(1 row)
```

### PASO 4: Desplegar Environment GREEN (10 min)

Tenemos dos ambientes: **BLUE** (actual) y **GREEN** (nuevo).

```bash
# Actualizar manifests Kubernetes
kubectl set image deployment/erp-core-green \
  backend=registry.sajet.us/erp-core-backend:${VERSION} \
  frontend=registry.sajet.us/erp-core-frontend:${VERSION} \
  -n production

# Esperar a que pods estén ready
kubectl rollout status deployment/erp-core-green -n production --timeout=5m

# Verificar logs
kubectl logs -l app=erp-core-green -n production --tail=50
```

**Validación**:
```bash
# Verificar health checks
curl -s https://green.sajet.us/api/health | jq .status

# Output esperado:
# {
#   "status": "healthy",
#   "database": "connected",
#   "timestamp": "2026-02-17T..."
# }
```

### PASO 5: Smoke Tests (5 min)

```bash
# Test básicos en GREEN
./tests/smoke_tests.sh https://green.sajet.us

# Checks incluyen:
# - JWT auth working
# - Dashboard endpoints responding
# - Database connectivity
# - Cloudflare tunnel active
```

**Expected output**:
```
✓ Auth endpoint: PASS
✓ Dashboard all: PASS (P50: 342ms)
✓ Tenants list: PASS
✓ Health check: PASS
═══════════════════════════════════
All smoke tests: PASS ✓
Proceed to traffic shifting
```

### PASO 6: Canary Deployment - 10% Traffic (3 min)

```bash
# Actualizar Ingress para routing 90% BLUE / 10% GREEN
kubectl patch ingress erp-core-ingress -n production --type merge -p '
{
  "spec": {
    "rules": [
      {
        "host": "app.sajet.us",
        "http": {
          "paths": [
            {
              "path": "/",
              "backend": {
                "service": {
                  "name": "erp-core-blue",
                  "port": {"number": 443}
                },
                "weight": 90
              }
            },
            {
              "path": "/",
              "backend": {
                "service": {
                  "name": "erp-core-green",
                  "port": {"number": 443}
                },
                "weight": 10
              }
            }
          ]
        }
      }
    ]
  }
}
'

# Verificar distribución
kubectl get endpoints erp-core-blue erp-core-green -n production
```

**Monitoreo (5 min)**:
```bash
# Watch metrics en tiempo real
watch 'kubectl top pods -n production | grep erp-core'

# Verificar error rates en Prometheus
curl 'http://prometheus.sajet.us/api/v1/query?query=rate(http_requests_total{job=\"erp-core-green\",status=~\"5..\"}[5m])'

# Esperado: error_rate < 0.5%
```

### PASO 7: Canary Deployment - 50% Traffic (5 min)

Si 10% fue OK, aumentar a 50%:

```bash
kubectl patch ingress erp-core-ingress -n production --type merge -p '
{
  "spec": {
    "rules": [{
      "host": "app.sajet.us",
      "http": {
        "paths": [
          {"path": "/", "backend": {...}, "weight": 50},
          {"path": "/", "backend": {...}, "weight": 50}
        ]
      }
    }]
  }
}
'
```

**Monitoreo (5 min)**:
```bash
# Verificar P95 latencia
curl 'http://prometheus.sajet.us/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'

# Esperado: < 1.5 segundos
```

### PASO 8: Full Cutover - 100% GREEN (5 min)

Si 50% fue OK:

```bash
kubectl patch ingress erp-core-ingress -n production --type merge -p '
{
  "spec": {
    "rules": [{
      "host": "app.sajet.us",
      "http": {
        "paths": [
          {
            "path": "/",
            "backend": {
              "service": {
                "name": "erp-core-green",
                "port": {"number": 443}
              },
              "weight": 100
            }
          }
        ]
      }
    }]
  }
}
'

echo "✓ Full cutover to GREEN completed"
```

**Verificación final**:
```bash
# Verificar que BLUE no recibe tráfico
kubectl logs deployment/erp-core-blue -n production --tail=20 | grep "request" | wc -l
# Esperado: 0

# Verificar GREEN recibe todo el tráfico
kubectl logs deployment/erp-core-green -n production --tail=100 | grep "request" | tail -10
```

### PASO 9: Monitoreo Post-Deploy (30 min)

```bash
# Dashboard Grafana
open "https://grafana.sajet.us/d/erp-core-monitoring"

# Métricas críticas a vigilar:
# - Request rate: baseline ± 5%
# - Error rate: < 0.5%
# - P50 latencia: < 500ms
# - P95 latencia: < 1.5s
# - Database connections: stable
# - CPU/Memory: normal
```

**Alert escalation**:
- ⚠️ Error rate > 1% → **Rollback inmediato**
- ⚠️ Latencia P95 > 3s → **Rollback inmediato**
- ⚠️ Database errors > 5 → **Rollback inmediato**

### PASO 10: Decommission BLUE (después de 24h)

```bash
# Mantener BLUE disponible por 24 horas mínimo
# Luego, limpiar recursos

kubectl delete deployment erp-core-blue -n production
kubectl delete service erp-core-blue -n production

# Backup de BLUE (por si acaso)
kubectl get deployment erp-core-blue -o yaml > backup-blue-$(date +%s).yaml
```

---

## 🔄 Rollback Procedures

### Rollback Inmediato (< 2 min)

Si algo sale mal **durante el deployment**:

```bash
# Option 1: Revert traffic to BLUE (instantaneous)
kubectl patch ingress erp-core-ingress -n production --type merge -p '
{
  "spec": {
    "rules": [{
      "host": "app.sajet.us",
      "http": {
        "paths": [{
          "path": "/",
          "backend": {
            "service": {"name": "erp-core-blue", "port": {"number": 443}},
            "weight": 100
          }
        }]
      }
    }]
  }
}
'

echo "✓ Rollback to BLUE completed in <30 segundos"
```

### Rollback Database (si migration falló)

```bash
# PostgreSQL point-in-time recovery
psql postgresql://jeturing:${DB_PASSWORD}@prod-db.sajet.us/erp_core_db << EOF
-- Verificar estado antes
SELECT version FROM alembic_version;

-- Downgrade (requiere que sea definido en Alembic)
-- alembic downgrade -1  # En sentido opuesto

-- O restaurar desde backup
pg_restore --clean --if-exists \
  -d erp_core_db \
  /backups/erp_core_db_pre_deploy_$(date +%Y%m%d).dump
EOF
```

### Full System Rollback (última opción)

```bash
# Restaurar deployment BLUE a versión anterior
kubectl set image deployment/erp-core-blue \
  backend=registry.sajet.us/erp-core-backend:v1.2.0 \
  frontend=registry.sajet.us/erp-core-frontend:v1.2.0 \
  -n production

kubectl rollout status deployment/erp-core-blue -n production

# Revert traffic
kubectl patch ingress ... (ver arriba)

# Comunicar a team
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
  -d '{"text":"🚨 FULL ROLLBACK executed. Back to v1.2.0"}'
```

---

## 📊 Post-Deployment Validation

**After 24h**:

```bash
# Reporte final
cat << EOF
╔════════════════════════════════════════════════╗
║       Post-Deployment Report - v1.3.0          ║
╚════════════════════════════════════════════════╝

Uptime:                  99.98%
Error rate:              0.02%
P50 latencia:            342ms ✓
P95 latencia:            1.2s ✓
New users onboarded:     5
Issues reported:         0

Status: 🟢 HEALTHY - Ready for next release

Fecha: $(date)
EOF
```

---

## 🎯 Timelineexpected

| Paso | Durración | Acción |
|------|-----------|--------|
| 1. Tag release | 5 min | Manual |
| 2. Build images | 10 min | CI/CD automático |
| 3. DB migrations | 5 min | Manual con validación |
| 4. Deploy GREEN | 10 min | Kubernetes rollout |
| 5. Smoke tests | 5 min | Automated tests |
| 6. 10% canary | 5 min + 5min wait | Manual patch + monitor |
| 7. 50% canary | 5 min + 5min wait | Manual patch + monitor |
| 8. 100% cutover | 5 min | Manual patch |
| 9. Monitor post | 30 min | Continuous watch |
| 10. Cleanup | 5 min | Manual (después 24h) |

**Total**: ~90 minutos (1.5 horas)

---

## 📱 Communication Checklist

- [ ] **T-1h**: Slack @channel notificación
- [ ] **T-0**: Start deployment message
- [ ] **T+10min**: Canary 10% confirmation
- [ ] **T+20min**: Canary 50% confirmation
- [ ] **T+30min**: 100% cutover confirmation
- [ ] **T+1h**: All-clear message
- [ ] **T+24h**: Post-deployment report

**Template**:
```
🚀 Deployment Started: v1.3.0
├─ Database migrations: IN PROGRESS
├─ Green environment: DEPLOYING
├─ Smoke tests: PENDING
└─ Traffic shift: PENDING (will start in 10 min)

Monitor: https://grafana.sajet.us/d/erp-core-monitoring
Rollback: Available if needed
ETA cutover: 14:45 UTC
```

---

## 🛠️ Troubleshooting

### Pods no inician
```bash
kubectl describe pod <pod-name> -n production
kubectl logs <pod-name> -n production --previous
```

### Database migration falló
```bash
# Ver qué migration falló
alembic current
alembic history

# Revertir última migration
alembic downgrade -1
```

### Traffic no está siendo balanceado
```bash
# Verificar ingress configuration
kubectl get ingress -n production -o yaml

# Rebuild ingress controller
kubectl rollout restart deployment/ingress-nginx -n ingress-nginx
```

---

## 📞 Emergency Contacts

- **DevOps Lead**: [nombre] (+1-XXX-XXX-XXXX)
- **Database Admin**: [nombre] (+1-XXX-XXX-XXXX)
- **On-Call**: Slack #incidents

---

**Versión**: 1.0  
**Última actualización**: 2026-02-17  
**Próxima revisión**: Después de primer deployment
