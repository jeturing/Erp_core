#!/usr/bin/env python3
"""
Database Migration: Create custom_domains table
Ejecutar en PCT 160 (10.10.10.20) contra erp_core_db

Uso:
    python3 migrate_custom_domains.py

O directamente con psql:
    psql -h 10.10.10.20 -U sajet_admin -d erp_core_db -f create_custom_domains.sql
"""

import os
import sys
from datetime import datetime

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models.database import engine, Base


SQL_CREATE_TABLE = """
-- Migration: Create custom_domains table
-- Date: {date}
-- Description: Sistema de dominios personalizados para clientes

-- Crear enum para estado de verificación
DO $$ BEGIN
    CREATE TYPE domain_verification_status AS ENUM ('pending', 'verifying', 'verified', 'failed', 'expired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Crear tabla custom_domains
CREATE TABLE IF NOT EXISTS custom_domains (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    tenant_deployment_id INTEGER,
    
    -- Dominios
    external_domain VARCHAR(255) NOT NULL UNIQUE,
    sajet_subdomain VARCHAR(100) NOT NULL UNIQUE,
    
    -- Verificación
    verification_status domain_verification_status DEFAULT 'pending',
    verification_token VARCHAR(255),
    verified_at TIMESTAMP,
    
    -- Configuración Cloudflare
    cloudflare_dns_record_id VARCHAR(100),
    cloudflare_configured BOOLEAN DEFAULT FALSE,
    tunnel_ingress_configured BOOLEAN DEFAULT FALSE,
    
    -- SSL
    ssl_status VARCHAR(50) DEFAULT 'pending',
    ssl_certificate_id VARCHAR(100),
    
    -- Estado
    is_active BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- Configuración de destino
    target_node_ip VARCHAR(50) DEFAULT 'localhost',
    target_port INTEGER DEFAULT 8069,
    
    -- Auditoría
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign Keys (con ON DELETE)
    CONSTRAINT fk_custom_domain_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    CONSTRAINT fk_custom_domain_deployment 
        FOREIGN KEY (tenant_deployment_id) REFERENCES tenant_deployments(id) ON DELETE SET NULL
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_custom_domains_customer ON custom_domains(customer_id);
CREATE INDEX IF NOT EXISTS idx_custom_domains_external ON custom_domains(external_domain);
CREATE INDEX IF NOT EXISTS idx_custom_domains_sajet ON custom_domains(sajet_subdomain);
CREATE INDEX IF NOT EXISTS idx_custom_domains_active ON custom_domains(is_active);
CREATE INDEX IF NOT EXISTS idx_custom_domains_status ON custom_domains(verification_status);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_custom_domains_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_custom_domains_updated ON custom_domains;
CREATE TRIGGER trigger_custom_domains_updated
    BEFORE UPDATE ON custom_domains
    FOR EACH ROW
    EXECUTE FUNCTION update_custom_domains_timestamp();

-- Actualizar tabla customers si faltan columnas
DO $$
BEGIN
    -- Agregar columna plan si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customers' AND column_name = 'plan') THEN
        ALTER TABLE customers ADD COLUMN plan VARCHAR(50) DEFAULT 'basic';
    END IF;
    
    -- Agregar columna status si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customers' AND column_name = 'status') THEN
        ALTER TABLE customers ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    -- Agregar columna phone si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customers' AND column_name = 'phone') THEN
        ALTER TABLE customers ADD COLUMN phone VARCHAR(50);
    END IF;
    
    -- Agregar columna notes si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customers' AND column_name = 'notes') THEN
        ALTER TABLE customers ADD COLUMN notes TEXT;
    END IF;
END $$;

-- Actualizar tabla subscriptions si faltan columnas
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'subscriptions' AND column_name = 'monthly_amount') THEN
        ALTER TABLE subscriptions ADD COLUMN monthly_amount NUMERIC(10,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'subscriptions' AND column_name = 'currency') THEN
        ALTER TABLE subscriptions ADD COLUMN currency VARCHAR(10) DEFAULT 'USD';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'subscriptions' AND column_name = 'current_period_start') THEN
        ALTER TABLE subscriptions ADD COLUMN current_period_start TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'subscriptions' AND column_name = 'current_period_end') THEN
        ALTER TABLE subscriptions ADD COLUMN current_period_end TIMESTAMP;
    END IF;
END $$;

-- Comentarios para documentación
COMMENT ON TABLE custom_domains IS 'Dominios personalizados de clientes que apuntan a subdominios de sajet.us';
COMMENT ON COLUMN custom_domains.external_domain IS 'Dominio del cliente (ej: www.impulse-max.com)';
COMMENT ON COLUMN custom_domains.sajet_subdomain IS 'Subdominio generado en sajet.us (ej: impulse-max)';
COMMENT ON COLUMN custom_domains.verification_status IS 'Estado de verificación del CNAME';
COMMENT ON COLUMN custom_domains.target_node_ip IS 'IP del nodo PCT donde está el tenant Odoo';
COMMENT ON COLUMN custom_domains.target_port IS 'Puerto del servicio Odoo (default 8069)';

-- Estadísticas
SELECT 'Migration completed successfully' as status, 
       (SELECT COUNT(*) FROM custom_domains) as existing_domains;
"""


def run_migration():
    """Ejecuta la migración"""
    print("=" * 60)
    print("DATABASE MIGRATION: custom_domains table")
    print("=" * 60)
    print(f"Target: {engine.url}")
    print(f"Date: {datetime.now().isoformat()}")
    print()
    
    sql = SQL_CREATE_TABLE.format(date=datetime.now().isoformat())
    
    try:
        with engine.connect() as conn:
            # Ejecutar cada statement separadamente
            statements = sql.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    try:
                        conn.execute(text(stmt))
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            print(f"Warning: {e}")
            
            conn.commit()
            
            # Verificar resultado
            result = conn.execute(text("SELECT COUNT(*) FROM custom_domains"))
            count = result.scalar()
            
            print("✅ Migration completed successfully!")
            print(f"   Table custom_domains exists with {count} records")
            
            # Mostrar estructura
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'custom_domains'
                ORDER BY ordinal_position
            """))
            
            print("\n   Columns:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True


def export_sql():
    """Exporta el SQL a un archivo"""
    sql = SQL_CREATE_TABLE.format(date=datetime.now().isoformat())
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'create_custom_domains.sql'
    )
    
    with open(output_path, 'w') as f:
        f.write(sql)
    
    print(f"SQL exported to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--export':
        export_sql()
    else:
        run_migration()
