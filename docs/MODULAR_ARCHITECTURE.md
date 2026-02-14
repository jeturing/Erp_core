# MODULAR ARCHITECTURE

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Arquitectura

## Objetivo
Arquitectura modular actual de routers y servicios.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- Routers FastAPI en app/routes/*
- Servicios en app/services/*
- SPA en frontend/src/*

## Operacion
- app/main.py como entrypoint
- Montaje static en /static

## Referencias
- `README.md`
- `docs/INDICE.md`
