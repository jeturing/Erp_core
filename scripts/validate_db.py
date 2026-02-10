#!/usr/bin/env python3
"""
Script de validación de conexión a PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def validate_connection():
    """Valida la conexión a la base de datos PostgreSQL"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado en .env")
        return False
    
    print(f"📡 Conectando a: {database_url.replace('321Abcd', '***')}")
    
    try:
        # Crear engine
        engine = create_engine(database_url)
        
        # Probar conexión
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT current_database(), current_user, inet_server_addr(), version()"
            ))
            row = result.fetchone()
            
            print("\n✅ CONEXIÓN EXITOSA")
            print("=" * 60)
            print(f"📚 Base de datos: {row[0]}")
            print(f"👤 Usuario: {row[1]}")
            print(f"🌐 IP del servidor: {row[2]}")
            print(f"🐘 PostgreSQL version: {row[3][:50]}...")
            print("=" * 60)
            
            # Verificar tablas existentes
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = result.fetchall()
            
            if tables:
                print(f"\n📋 Tablas encontradas ({len(tables)}):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠️  No se encontraron tablas. Ejecuta las migraciones.")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN: {e}")
        return False

if __name__ == "__main__":
    success = validate_connection()
    sys.exit(0 if success else 1)
