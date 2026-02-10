#!/usr/bin/env python3
"""
Test cases for odoo_provisioner validation
Ejecutar: python test_provisioner.py
"""

import pytest
import asyncio
from app.services.odoo_provisioner import (
    _validate_subdomain,
    _validate_email,
    _validate_company_name,
    _validate_ip_address,
    _validate_port,
    ValidationError,
    ProvisioningError
)


class TestSubdomainValidation:
    """Tests para validación de subdomain"""
    
    def test_valid_subdomain(self):
        """Subdomains válidos no lanzan error"""
        valid = ["acme", "client-123", "my-company", "a", "a1b2c3"]
        for subdomain in valid:
            try:
                _validate_subdomain(subdomain)
            except ValidationError:
                pytest.fail(f"'{subdomain}' debería ser válido")
    
    def test_invalid_subdomain_reserved(self):
        """Subdomains reservados lanzan error"""
        reserved = ["admin", "api", "www", "mail", "ftp", "ns", "root"]
        for subdomain in reserved:
            with pytest.raises(ValidationError, match="reservado"):
                _validate_subdomain(subdomain)
    
    def test_invalid_subdomain_chars(self):
        """Subdomains con caracteres inválidos lanzan error"""
        invalid = ["admin@", "client_123", "my company", "acme!"]
        for subdomain in invalid:
            with pytest.raises(ValidationError):
                _validate_subdomain(subdomain)
    
    def test_invalid_subdomain_hyphens(self):
        """Subdomains que empiezan/terminan con guión lanzan error"""
        invalid = ["-acme", "acme-", "-acme-"]
        for subdomain in invalid:
            with pytest.raises(ValidationError):
                _validate_subdomain(subdomain)
    
    def test_invalid_subdomain_length(self):
        """Subdomains > 63 caracteres lanzan error"""
        long_subdomain = "a" * 64
        with pytest.raises(ValidationError, match="máximo 63"):
            _validate_subdomain(long_subdomain)
    
    def test_subdomain_empty(self):
        """Subdomain vacío lanza error"""
        with pytest.raises(ValidationError):
            _validate_subdomain("")
    
    def test_subdomain_none(self):
        """Subdomain None lanza error"""
        with pytest.raises(ValidationError):
            _validate_subdomain(None)


class TestEmailValidation:
    """Tests para validación de email"""
    
    def test_valid_emails(self):
        """Emails válidos no lanzan error"""
        valid = [
            "admin@acme.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "john_doe@company.org"
        ]
        for email in valid:
            try:
                _validate_email(email)
            except ValidationError:
                pytest.fail(f"'{email}' debería ser válido")
    
    def test_invalid_email_format(self):
        """Emails con formato inválido lanzan error"""
        invalid = [
            "notanemail",
            "@example.com",
            "user@",
            "user..name@example.com",
            "user@.com"
        ]
        for email in invalid:
            with pytest.raises(ValidationError, match="inválido"):
                _validate_email(email)
    
    def test_invalid_email_length(self):
        """Emails > 254 caracteres lanzan error"""
        long_email = "a" * 250 + "@test.com"
        with pytest.raises(ValidationError, match="muy largo"):
            _validate_email(long_email)
    
    def test_email_empty(self):
        """Email vacío lanza error"""
        with pytest.raises(ValidationError):
            _validate_email("")
    
    def test_email_none(self):
        """Email None lanza error"""
        with pytest.raises(ValidationError):
            _validate_email(None)


class TestCompanyNameValidation:
    """Tests para validación de company name"""
    
    def test_valid_company_names(self):
        """Company names válidos no lanzan error"""
        valid = [
            "Acme Corp",
            "Tech Company Ltd.",
            "My Business 123",
            "Empresa S.A."
        ]
        for name in valid:
            try:
                _validate_company_name(name)
            except ValidationError:
                pytest.fail(f"'{name}' debería ser válido")
    
    def test_invalid_company_name_short(self):
        """Company name < 2 caracteres lanza error"""
        with pytest.raises(ValidationError, match="mínimo 2"):
            _validate_company_name("A")
    
    def test_invalid_company_name_long(self):
        """Company name > 255 caracteres lanza error"""
        long_name = "A" * 256
        with pytest.raises(ValidationError, match="máximo 255"):
            _validate_company_name(long_name)
    
    def test_company_name_empty(self):
        """Company name vacío lanza error"""
        with pytest.raises(ValidationError):
            _validate_company_name("")
    
    def test_company_name_none(self):
        """Company name None lanza error"""
        with pytest.raises(ValidationError):
            _validate_company_name(None)


class TestIPValidation:
    """Tests para validación de IP"""
    
    def test_valid_ipv4(self):
        """IPv4 válidas no lanzan error"""
        valid = [
            "172.16.16.105",
            "192.168.1.1",
            "10.0.0.1",
            "127.0.0.1",
            "255.255.255.255"
        ]
        for ip in valid:
            try:
                _validate_ip_address(ip)
            except ValidationError:
                pytest.fail(f"'{ip}' debería ser válida")
    
    def test_valid_ipv6(self):
        """IPv6 básicas no lanzan error"""
        valid = ["::1", "2001:db8::1"]
        for ip in valid:
            try:
                _validate_ip_address(ip)
            except ValidationError:
                pytest.fail(f"'{ip}' debería ser válida")
    
    def test_invalid_ip_octets(self):
        """IPs con octetos > 255 lanzan error"""
        invalid = [
            "256.1.1.1",
            "1.1.1.256",
            "300.168.1.1"
        ]
        for ip in invalid:
            with pytest.raises(ValidationError, match="inválida"):
                _validate_ip_address(ip)
    
    def test_invalid_ip_format(self):
        """IPs con formato inválido lanzan error"""
        invalid = [
            "192.168.1",
            "192.168.1.1.1",
            "notanip"
        ]
        for ip in invalid:
            with pytest.raises(ValidationError):
                _validate_ip_address(ip)
    
    def test_ip_empty(self):
        """IP vacía lanza error"""
        with pytest.raises(ValidationError):
            _validate_ip_address("")
    
    def test_ip_none(self):
        """IP None lanza error"""
        with pytest.raises(ValidationError):
            _validate_ip_address(None)


class TestPortValidation:
    """Tests para validación de puerto"""
    
    def test_valid_ports(self):
        """Puertos válidos no lanzan error"""
        valid = [1, 80, 443, 8069, 8080, 65535]
        for port in valid:
            try:
                _validate_port(port)
            except ValidationError:
                pytest.fail(f"'{port}' debería ser válido")
    
    def test_invalid_port_zero(self):
        """Puerto 0 lanza error"""
        with pytest.raises(ValidationError, match="debe estar entre"):
            _validate_port(0)
    
    def test_invalid_port_negative(self):
        """Puerto negativo lanza error"""
        with pytest.raises(ValidationError):
            _validate_port(-1)
    
    def test_invalid_port_too_high(self):
        """Puerto > 65535 lanza error"""
        with pytest.raises(ValidationError, match="65535"):
            _validate_port(65536)
    
    def test_invalid_port_type(self):
        """Puerto no entero lanza error"""
        with pytest.raises(ValidationError, match="debe ser un entero"):
            _validate_port("8069")


# ===== INTEGRATION TESTS =====

class TestIntegration:
    """Tests de integración"""
    
    @pytest.mark.asyncio
    async def test_provision_with_valid_data(self):
        """Provisioning con datos válidos (requiere .env)"""
        # Este test requiere .env configurado
        pytest.skip("Requiere .env y BD configuradas")
    
    @pytest.mark.asyncio
    async def test_provision_with_invalid_subdomain(self):
        """Provisioning con subdomain inválido retorna error"""
        pytest.skip("Test de integración completo")


# ===== CLI TEST RUNNER =====

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])
