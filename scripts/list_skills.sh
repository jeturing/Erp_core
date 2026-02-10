#!/usr/bin/env bash

set -euo pipefail

# Script para listar las skills instaladas (global y local)

echo "Skills globales (si existe): ~/.claude/skills/"
if [ -d "$HOME/.claude/skills" ]; then
  ls -la "$HOME/.claude/skills"
else
  echo "No existe ~/.claude/skills/"
fi

echo
echo "Skills locales (proyecto): .claude/skills/"
if [ -d ".claude/skills" ]; then
  ls -la ".claude/skills"
else
  echo "No existe .claude/skills/ en el proyecto actual"
fi
