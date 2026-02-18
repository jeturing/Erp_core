#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/onboarding-system')

try:
    from app.routes import auth
    print("✅ auth module OK")
    
    from app.routes import dashboard  
    print("✅ dashboard module OK")
    
    from app.routes import tenants
    print("✅ tenants module OK")
    
    from app.routes import onboarding
    print("✅ onboarding module OK")
    
    from app import main
    print("✅ main module OK")
    
    print("\n🎉 Todos los módulos importados exitosamente!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
