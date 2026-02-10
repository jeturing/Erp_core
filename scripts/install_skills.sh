#!/usr/bin/env bash

set -euo pipefail

# Script para instalar una lista de skills recomendadas.
# Revisa y descomenta las líneas que quieras ejecutar.

echo "Comprobando node y npm..."
if ! command -v node >/dev/null 2>&1; then
  echo "Node no está instalado. Instala Node.js antes de continuar." >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "npx no disponible. Asegúrate de tener npm/node correctamente instalados." >&2
  exit 1
fi

# Ejemplos - descomenta según necesites

# Skill #1 - React best practices (proyecto local)
 npx skills add vercel-labs/agent-skills@vercel-react-best-practices

# Skill #3 - Web design guidelines (global)
 npx skills add vercel-labs/agent-skills@web-design-guidelines -g -y

# Skill #6 - Frontend design de Anthropic
npx skills add anthropics/skills@frontend-design -g -y

# Marketing stack
# npx skills add coreyhaines31/marketingskills@seo-audit -g -y
# npx skills add coreyhaines31/marketingskills@copywriting -g -y

# Desarrollo full-stack
# npx skills add vercel-labs/next-skills@next-best-practices -g -y
# npx skills add supabase/agent-skills@supabase-postgres-best-practices -g -y
npx skills add anthropics/skills@webapp-testing -g -y

echo "Script preparado. Edita y descomenta las líneas deseadas, luego ejecuta:"
echo "bash scripts/install_skills.sh"


npx skills add inference-sh/skills@inference-sh
