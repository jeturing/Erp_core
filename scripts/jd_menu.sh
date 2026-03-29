#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm
fi

PROJECT_ROOT=${PROJECT_ROOT:-/opt/Erp_core}
CATALOG="${PROJECT_ROOT}/scripts/jd_tenant_catalog.py"
MIGRATE="${PROJECT_ROOT}/scripts/jd_migrate_tenant.sh"
SAJET="${PROJECT_ROOT}/scripts/jd_sajet.sh"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

run_and_show() {
  local title="$1"
  shift
  local outfile="${temp_dir}/output.txt"
  if "$@" >"${outfile}" 2>&1; then
    whiptail --title "${title}" --textbox "${outfile}" 30 110 || true
  else
    whiptail --title "${title} (error)" --textbox "${outfile}" 30 110 || true
  fi
  return 0
}

show_text() {
  local title="$1"
  local outfile="${temp_dir}/output.txt"
  cat > "${outfile}"
  whiptail --title "${title}" --textbox "${outfile}" 30 110 || true
  return 0
}

confirm_and_migrate() {
  local tenant="$1"
  local pct="$2"
  if whiptail --title "Confirmar migración" --yesno "Migrar ${tenant} a dedicated_service en PCT ${pct}?\n\nEl flujo hará repair si falta tenant_deployment y luego provisionará/migrará automáticamente." 14 90; then
    run_and_show "M${pct} · ${tenant}" "${MIGRATE}" --pct "${pct}" "${tenant}"
  fi
}

confirm_and_restart_dedicated() {
  local tenant="$1"
  if whiptail --title "Confirmar reinicio" --yesno "Reiniciar solo el servicio dedicado de ${tenant}?\n\nEl flujo aborta si el tenant no está en dedicated_service para no tocar el servicio shared del nodo." 14 95; then
    run_and_show "Restart · ${tenant}" "${PYTHON_BIN}" "${CATALOG}" restart-dedicated "${tenant}"
  fi
}

tenant_actions() {
  local tenant="$1"
  while true; do
    local action
    action=$(whiptail --title "JD · ${tenant}" --menu "Acción para ${tenant}" 22 110 12 \
      "FLOW" "Explica el flujo correcto de migración dedicada" \
      "STATUS" "Ver estado customer/subscription/deployment" \
      "DSTATUS" "Ver estado dedicado: servicio, puertos, nodo" \
      "DOMAINS" "Ver dominios vinculados desde BDA" \
      "RESTART" "Reiniciar solo el servicio dedicado del tenant" \
      "REPAIR105" "Crea/repara tenant_deployment en PCT 105" \
      "REPAIR161" "Crea/repara tenant_deployment en PCT 161" \
      "M105" "Auto: repair + puertos + dedicated en PCT 105" \
      "M161" "Auto: repair + puertos + dedicated en PCT 161" \
      "BACK" "Volver" \
      3>&1 1>&2 2>&3) || return 0

    case "${action}" in
      FLOW)
        show_text "Flow · ${tenant}" <<EOF
Flujo correcto para ${tenant}

1. STATUS
   Revisa si existe customer, subscription y tenant_deployment.

2. Si falta tenant_deployment:
   Usa REPAIR105 o REPAIR161 segun el nodo destino.
   Esto crea el registro base en tenant_deployments.

3. M105 o M161
   Este es el flujo operativo principal.

   - Si el tenant ya esta en ese mismo nodo:
     usa provision-dedicated
     asigna puertos dedicados HTTP/CHAT
     crea conf per-tenant
     crea/activa systemd
     configura routing nginx
     separa el tenant del flujo normal shared_pool

   - Si el tenant va a otro nodo:
     usa migration/start con target_runtime_mode=dedicated_service
     orquesta la migracion y deja el runtime separado en el nodo destino

4. DOMAINS
   Verifica dominios vinculados y routing despues del cambio.

Regla practica:
- mismo nodo: REPAIR si hace falta, luego M105/M161
- otro nodo: M105/M161 basta; el wrapper decide el flujo
EOF
        ;;
      STATUS)
        run_and_show "Estado · ${tenant}" "${PYTHON_BIN}" "${CATALOG}" status "${tenant}"
        ;;
      DSTATUS)
        run_and_show "Dedicated · ${tenant}" "${PYTHON_BIN}" "${CATALOG}" dedicated-status "${tenant}"
        ;;
      DOMAINS)
        run_and_show "Dominios · ${tenant}" "${PYTHON_BIN}" "${CATALOG}" linked-domains "${tenant}"
        ;;
      RESTART)
        confirm_and_restart_dedicated "${tenant}"
        ;;
      REPAIR105)
        run_and_show "Repair 105 · ${tenant}" "${PYTHON_BIN}" "${CATALOG}" ensure-deployment "${tenant}" --pct 105
        ;;
      REPAIR161)
        run_and_show "Repair 161 · ${tenant}" "${PYTHON_BIN}" "${CATALOG}" ensure-deployment "${tenant}" --pct 161
        ;;
      M105)
        run_and_show "M105 · ${tenant}" "${MIGRATE}" --pct 105 "${tenant}"
        ;;
      M161)
        run_and_show "M161 · ${tenant}" "${MIGRATE}" --pct 161 "${tenant}"
        ;;
      BACK)
        return 0
        ;;
    esac
  done
}

dedicated_browser() {
  local mode="$1"
  local search=""
  while true; do
    local options_file="${temp_dir}/dedicated.tsv"
    "${PYTHON_BIN}" "${CATALOG}" list-dedicated --search "${search}" > "${options_file}"

    if [[ ! -s "${options_file}" ]]; then
      whiptail --msgbox "No hay tenants en dedicated_service${search:+ para '${search}'}" 10 80 || true
      return 0
    fi

    local -a menu_items=()
    while IFS=$'\t' read -r tag desc; do
      [[ -z "${tag}" ]] && continue
      menu_items+=("${tag}" "${desc}")
    done < "${options_file}"
    menu_items+=("__FILTER__" "Cambiar filtro")
    menu_items+=("__BACK__" "Volver")

    local title action_desc selected
    if [[ "${mode}" == "restart" ]]; then
      title="JD · Reinicio Dedicado"
      action_desc="Selecciona tenant dedicado para reiniciar su servicio"
    else
      title="JD · Dedicados"
      action_desc="Selecciona tenant dedicado para ver detalle"
    fi

    selected=$(whiptail --title "${title}" --menu "${action_desc}" 28 125 18 "${menu_items[@]}" 3>&1 1>&2 2>&3) || return 0
    case "${selected}" in
      __FILTER__)
        search=$(whiptail --inputbox "Filtro opcional para tenants dedicados" 10 80 "${search}" 3>&1 1>&2 2>&3) || search=""
        ;;
      __BACK__)
        return 0
        ;;
      *)
        if [[ "${mode}" == "restart" ]]; then
          confirm_and_restart_dedicated "${selected}"
        else
          run_and_show "Dedicated · ${selected}" "${PYTHON_BIN}" "${CATALOG}" dedicated-status "${selected}"
        fi
        ;;
    esac
  done
}

tenant_browser() {
  local search=""
  while true; do
    search=$(whiptail --inputbox "Filtro de tenant o BDA" 10 80 "${search}" 3>&1 1>&2 2>&3) || return 0

    local options_file="${temp_dir}/tenants.tsv"
    "${PYTHON_BIN}" "${CATALOG}" list --search "${search}" > "${options_file}"

    if [[ ! -s "${options_file}" ]]; then
      whiptail --msgbox "No hay resultados para '${search}'" 10 60
      continue
    fi

    local -a menu_items=()
    while IFS=$'\t' read -r tag desc; do
      [[ -z "${tag}" ]] && continue
      menu_items+=("${tag}" "${desc}")
    done < "${options_file}"
    menu_items+=("__SEARCH__" "Cambiar filtro")
    menu_items+=("__BACK__" "Volver")

    local selected
    selected=$(whiptail --title "JD · Tenants" --menu "Selecciona tenant/BDA" 26 120 16 "${menu_items[@]}" 3>&1 1>&2 2>&3) || return 0
    case "${selected}" in
      __SEARCH__)
        continue
        ;;
      __BACK__)
        return 0
        ;;
      *)
        tenant_actions "${selected}"
        ;;
    esac
  done
}

migration_browser() {
  local pct="$1"
  local search=""
  while true; do
    local options_file="${temp_dir}/migratable-${pct}.tsv"
    "${PYTHON_BIN}" "${CATALOG}" list-migratable --pct "${pct}" --search "${search}" > "${options_file}"

    if [[ ! -s "${options_file}" ]]; then
      if [[ -n "${search}" ]]; then
        whiptail --msgbox "No hay tenants migrables para '${search}' en PCT ${pct}" 10 70 || true
      else
        whiptail --msgbox "No hay tenants migrables disponibles para PCT ${pct}" 10 70 || true
      fi
      return 0
    fi

    local -a menu_items=()
    while IFS=$'\t' read -r tag desc; do
      [[ -z "${tag}" ]] && continue
      menu_items+=("${tag}" "${desc}")
    done < "${options_file}"
    menu_items+=("__FILTER__" "Cambiar filtro")
    menu_items+=("__BACK__" "Volver")

    local selected
    selected=$(whiptail --title "JD · Migrar a PCT ${pct}" --menu "Selecciona tenant para migración automática" 28 125 18 "${menu_items[@]}" 3>&1 1>&2 2>&3) || return 0
    case "${selected}" in
      __FILTER__)
        search=$(whiptail --inputbox "Filtro opcional para PCT ${pct}" 10 80 "${search}" 3>&1 1>&2 2>&3) || search=""
        ;;
      __BACK__)
        return 0
        ;;
      *)
        confirm_and_migrate "${selected}" "${pct}"
        ;;
    esac
  done
}

while true; do
  choice=$(whiptail --title "JD" --menu "Centro de acciones" 20 90 10 \
    "MIGRATE_105" "Lista rápida: migrar tenants a dedicated en PCT 105" \
    "MIGRATE_161" "Lista rápida: migrar tenants a dedicated en PCT 161" \
    "DEDICATED" "Inventario vivo de tenants dedicados" \
    "RESTART_DEDICATED" "Reiniciar solo servicios dedicados por tenant" \
    "TENANTS" "Explorar tenants/BDA y acciones manuales" \
    "SAJET_STATUS" "Build/deploy SAJET: ver estado" \
    "SAJET_DEPLOY" "Build/deploy SAJET: ejecutar" \
    "EXIT" "Salir" \
    3>&1 1>&2 2>&3) || break

  case "${choice}" in
    MIGRATE_105)
      migration_browser "105"
      ;;
    MIGRATE_161)
      migration_browser "161"
      ;;
    DEDICATED)
      dedicated_browser "view"
      ;;
    RESTART_DEDICATED)
      dedicated_browser "restart"
      ;;
    TENANTS)
      tenant_browser
      ;;
    SAJET_STATUS)
      run_and_show "JD -sajet --status" "${SAJET}" --status
      ;;
    SAJET_DEPLOY)
      run_and_show "JD -sajet" "${SAJET}"
      ;;
    EXIT)
      exit 0
      ;;
  esac
done

exit 0
