# 06 - Infraestructura Proxmox

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Exponer estado de nodos/containers y ejecutar provisioning operativo desde panel admin.

## Disparador
- Frontend: `#/infrastructure`
- API: `/api/nodes/*`

## Secuencia ASCII

```text
[SPA Infrastructure]
   |
   | GET /api/nodes
   | GET /api/nodes/status
   | GET /api/nodes/containers/all
   v
[nodes.py + proxmox_manager.py]
   |
   +--> consulta API Proxmox
   +--> normaliza recursos (CPU/RAM/DISK)
   v
[Vista de cluster en SPA]
```

## Provisioning operativo

```text
[Admin action]
   |
   | POST /api/nodes/provision
   v
[Backend]
   |
   +--> selecciona nodo
   +--> crea/actualiza container
   +--> registra deployment
   v
[Estado final en dashboard]
```

## Errores típicos
- API token Proxmox inválido
- Nodos en mantenimiento/offline
- Falta de recursos (RAM/disk)
