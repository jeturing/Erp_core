# Instalación de Skills en VSCode

Este documento recoge los pasos y scripts para instalar y verificar "skills" (plugins para Claude/skills CLI) y usarlas desde VSCode.

## Requisito previo
Instala Node.js y el CLI de skills (si no lo tienes):

```bash
npm install -g @skills/cli
```

Si prefieres no instalar globalmente, puedes usar `npx` para ejecutar el CLI sin instalación previa.

## Comandos de instalación

Instalar una skill específica (ejemplos):

```bash
# Skill #1 - React best practices (proyecto local)
npx skills add vercel-labs/agent-skills@vercel-react-best-practices

# Skill #3 - Web design guidelines (global)
npx skills add vercel-labs/agent-skills@web-design-guidelines -g -y

# Skill #6 - Frontend design de Anthropic
npx skills add anthropics/skills@frontend-design -g -y
```

Instalar múltiples skills de alto impacto (ejemplo agrupado):

```bash
# Marketing stack
npx skills add coreyhaines31/marketingskills@seo-audit -g -y
npx skills add coreyhaines31/marketingskills@copywriting -g -y

# Desarrollo full-stack
npx skills add vercel-labs/next-skills@next-best-practices -g -y
npx skills add supabase/agent-skills@supabase-postgres-best-practices -g -y
npx skills add anthropics/skills@webapp-testing -g -y
```

## Verificación en VSCode

Una vez instaladas, las skills deben aparecer automáticamente en Claude Code.

Comandos útiles para verificar y buscar skills desde la CLI (o desde Claude):

```bash
# Listar skills instaladas (si el CLI soporta este comando)
/list-skills

# Buscar skills
/find-skills tailwind
/find-skills authentication
/find-skills api design
```

Si no tienes comandos directos, puedes listar los directorios donde se instalan:

```bash
# Global
ls -la ~/.claude/skills/

# Proyecto (local)
ls -la .claude/skills/
```

## Skills recomendadas por perfil

Ejemplos recomendados para roles de cybersecurity y desarrollo:

```bash
# Stack técnico
npx skills add anthropics/skills@skill-creator -g -y
npx skills add anthropics/skills@mcp-builder -g -y
npx skills add obra/superpowers@systematic-debugging -g -y
npx skills add wshobson/agents@sql-optimization-patterns -g -y

# Seguridad y arquitectura
npx skills add wshobson/agents@api-design-principles -g -y
npx skills add wshobson/agents@microservices-patterns -g -y
npx skills add wshobson/agents@auth-implementation-patterns -g -y

# Productividad
npx skills add softaworks/agent-toolkit@commit-work -g -y
npx skills add obra/superpowers@requesting-code-review -g -y
```

## Uso en VSCode

Las skills pueden activarse automáticamente por el contexto o invocarse directamente:

```bash
# Invocación directa desde la paleta/comando
/vercel-react-best-practices
/systematic-debugging
/api-design-principles
```

## Actualización y mantenimiento

```bash
# Verificar actualizaciones disponibles
npx skills check

# Actualizar todas las skills
npx skills update

# Desinstalar skill
npx skills remove vercel-labs/agent-skills@vercel-react-best-practices
```

## Ubicación de las Skills

- Global (`-g`): `~/.claude/skills/`
- Proyecto (local): `.claude/skills/` en el directorio del proyecto

Las skills globales están disponibles en todos tus proyectos VSCode; las locales solo en el proyecto específico.

## Scripts incluidos

Hay scripts en `scripts/` para automatizar la instalación y verificación (ver [scripts/install_skills.sh](scripts/install_skills.sh) y [scripts/list_skills.sh](scripts/list_skills.sh)).

## Notas y recomendaciones

- Revisa permisos y ubicación de Node/npm en macOS (puede requerir `sudo` para instalaciones globales o usar `nvm`).
- Usa `-g -y` para instalaciones globales sin prompts cuando sea seguro.
- Si trabajas en entornos corporativos, revisa proxies/registro de paquetes.

Si quieres, puedo mostrar cómo ejecutar los scripts localmente o prepararte un comando para copiar/pegar en tu terminal.
