# INSTALLAR SKILLS VSCODE

Estado: vigente
Validado: 2026-02-22
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Tooling

## Objetivo
Documento de referencia para tooling.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- scripts/install_skills.sh
- .agents/skills/*

## Operacion
- Uso opcional de skills en .agents/skills

### Skills disponibles
- [Full-Stack Consistency Guardian](../../.agents/skills/full-stack-consistency-guardian/SKILL.md)

### Uso recomendado (Skill Full-Stack)
1. Identificar contrato backend (Pydantic/Odoo)
2. Generar tipos TypeScript
3. Implementar estados completos: idle, loading, success, error
4. Validar request/response con el mismo criterio

### MCP Local (soporte tooling)
```bash
node mcp/api-server.js
```
Config: [mcp_config.json](../../mcp_config.json)

## Referencias
- `README.md`
- `docs/INDICE.md`
