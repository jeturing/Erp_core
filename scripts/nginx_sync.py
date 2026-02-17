#!/usr/bin/env python3
"""
nginx_sync.py — Fallback sync para dominios sin nginx configurado.
Corre en PCT160 (donde está el FastAPI) cada 5 minutos via cron/systemd.
Detecta dominios activos con nginx_configured=false y los configura.

Uso:
  python3 /opt/Erp_core/scripts/nginx_sync.py
  
Cron:
  */5 * * * * /usr/bin/python3 /opt/Erp_core/scripts/nginx_sync.py >> /var/log/nginx_sync.log 2>&1
"""

import sys
import os
import logging

# Agregar el path del proyecto
sys.path.insert(0, "/opt/Erp_core")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nginx_sync")


def main():
    logger.info("=" * 50)
    logger.info("Iniciando nginx_sync fallback")
    logger.info("=" * 50)

    try:
        from app.models.database import SessionLocal, CustomDomain, TenantDeployment
        from app.services.nginx_domain_configurator import NginxDomainConfigurator
    except ImportError as e:
        logger.error(f"Error importando módulos: {e}")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Buscar dominios activos sin nginx configurado
        domains = (
            db.query(CustomDomain)
            .filter(
                CustomDomain.is_active == True,
                CustomDomain.nginx_configured == False,
            )
            .all()
        )

        if not domains:
            logger.info("No hay dominios pendientes de configuración nginx")
            return

        logger.info(f"Encontrados {len(domains)} dominios pendientes de nginx")
        configurator = NginxDomainConfigurator()
        ok = 0
        fail = 0

        for domain in domains:
            # Resolver tenant info
            tenant_db = domain.sajet_subdomain
            tenant_subdomain = domain.sajet_subdomain

            if domain.tenant_deployment_id:
                deployment = (
                    db.query(TenantDeployment)
                    .filter(TenantDeployment.id == domain.tenant_deployment_id)
                    .first()
                )
                if deployment:
                    if deployment.database_name:
                        tenant_db = deployment.database_name
                    if deployment.subdomain:
                        tenant_subdomain = deployment.subdomain

            node_ip = domain.target_node_ip or "10.10.10.100"

            logger.info(f"Configurando {domain.external_domain} → {tenant_db}")
            result = configurator.configure_domain(
                external_domain=domain.external_domain,
                tenant_db=tenant_db,
                tenant_subdomain=tenant_subdomain,
                node_ip=node_ip,
            )

            if result.get("success"):
                domain.nginx_configured = True
                db.commit()
                ok += 1
                logger.info(f"  ✅ {domain.external_domain}")
            else:
                fail += 1
                logger.error(
                    f"  ❌ {domain.external_domain}: {result.get('error')}"
                )

        logger.info(f"Resultado: {ok} ok, {fail} fallos de {len(domains)} total")

    except Exception as e:
        logger.error(f"Error general: {e}")
    finally:
        db.close()

    logger.info("nginx_sync completado")


if __name__ == "__main__":
    main()
