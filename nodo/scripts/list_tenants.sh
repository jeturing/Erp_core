#!/bin/bash
# Listar todos los tenants en este nodo
# Uso: ./list_tenants.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Tenants en este nodo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DOMAIN="${1:-sajet.us}"

sudo -u postgres psql -t -c "
SELECT 
    datname as 'Database',
    pg_size_pretty(pg_database.dattablespace) as 'Tamaño',
    to_char(pg_stat_database.stats_reset, 'YYYY-MM-DD HH24:MI:SS') as 'Último Reset'
FROM pg_database
LEFT JOIN pg_stat_database ON pg_database.oid = pg_stat_database.datid
WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1')
ORDER BY datname;
" | column -t -s $'\t'

echo ""
echo "URLs de acceso:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1');" | while read db; do
    db=$(echo "$db" | xargs)
    if [ ! -z "$db" ]; then
        echo "  https://$db.$DOMAIN"
    fi
done
