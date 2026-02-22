# Frontend ERP Core

Estado: vigente  
Validado: 2026-02-22

Aplicacion SPA administrativa construida con Svelte 5 + TypeScript + Vite.

## Stack

- `svelte` 5
- `vite` 7
- `typescript` 5.9
- `tailwindcss` 3
- `chart.js` 4

## Estructura

```text
frontend/src/
├── lib/
│   ├── api/          # clientes HTTP tipados por dominio
│   ├── components/   # componentes UI reutilizables
│   ├── stores/       # estado global
│   ├── types/        # tipos compartidos
│   └── utils/        # helpers y formateadores
├── pages/            # vistas del panel admin
├── routes/           # login, dashboard y portales
├── App.svelte
└── main.ts
```

## Comandos

Instalar dependencias:

```bash
cd /opt/Erp_core/frontend
npm ci
```

Desarrollo local:

```bash
npm run dev
```

Chequeo tipado/linting de Svelte:

```bash
npm run check
```

Build de produccion:

```bash
npm run build
```

Preview local de build:

```bash
npm run preview
```

## Integracion con backend

- Base API esperada: `http://localhost:4443`
- Rutas protegidas dependen de cookie JWT emitida por `POST /api/auth/login`
- La build estatica se publica en `../static/spa/` usando `../scripts/build_static.sh`

## Referencias

- `README.md`
- `docs/01-frontend/ADMIN_DASHBOARD.md`
- `docs/INDICE.md`
