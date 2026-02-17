#!/usr/bin/env python3
"""
Load Testing Script - Sajet ERP Dashboard
Valida performance del endpoint consolidado /api/dashboard/all
Target: P50 < 500ms, P95 < 1.5s, P99 < 3s, error rate < 1%
"""

from locust import HttpUser, task, between
import json
import os
from datetime import datetime

class DashboardUser(HttpUser):
    """Simulador de usuario accediendo al dashboard"""
    
    wait_time = between(1, 3)  # Esperar 1-3 segundos entre requests
    
    def on_start(self):
        """Autenticación al iniciar"""
        # Mock JWT token para testing (debe reemplazarse con token real)
        self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
    
    @task(3)
    def dashboard_all(self):
        """Request al endpoint consolidado (3x frecuencia)"""
        with self.client.get(
            "/api/dashboard/all",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "metrics" in data and "tenants" in data and "infrastructure" in data:
                        response.success()
                    else:
                        response.failure(f"Estructura inválida: {list(data.keys())}")
                except Exception as e:
                    response.failure(f"JSON parse error: {str(e)}")
            elif response.status_code == 401:
                response.failure("Autenticación fallida")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def tenants_list(self):
        """Request al endpoint de tenants (1x frecuencia)"""
        with self.client.get(
            "/api/tenants?page=1&limit=10",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def metrics(self):
        """Request a métricas (1x frecuencia)"""
        with self.client.get(
            "/api/dashboard/metrics",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Load Testing Script - Sajet ERP Dashboard           ║
╚══════════════════════════════════════════════════════════════╝

Uso:
  locust -f load_test.py --host=http://localhost:4443 \\
    --users=100 --spawn-rate=10 --run-time=5m

Targets:
  • P50 latencia: < 500ms
  • P95 latencia: < 1.5s
  • P99 latencia: < 3s
  • Error rate: < 1%

Credenciales:
  • Token: Actualizar en on_start() con JWT real
  • Basada en datos staging

Endpoints testeados:
  1. GET /api/dashboard/all (3x peso)
  2. GET /api/tenants?page=1&limit=10 (1x peso)
  3. GET /api/dashboard/metrics (1x peso)

Parámetros:
  • 100 usuarios concurrentes
  • 10 usuarios por segundo de spawn rate
  • 5 minutos de duración
  • 1-3 segundos entre requests
    """)
