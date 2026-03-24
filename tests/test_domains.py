"""
Tests for custom domain verification flows.
"""
import asyncio

import dns.resolver

from app.models.database import CustomDomain, DomainVerificationStatus
from app.services.domain_manager import DomainManager


class TestDomainVerification:
    def test_external_domain_does_not_verify_from_internal_sajet_record(
        self,
        db_session,
        sample_customer,
        monkeypatch,
    ):
        domain = CustomDomain(
            customer_id=sample_customer.id,
            external_domain="boletly.com",
            sajet_subdomain="boletly",
            verification_status=DomainVerificationStatus.pending,
            cloudflare_configured=True,
            cloudflare_dns_record_id="cf-test",
            target_node_ip="localhost",
            target_port=8069,
            created_by="pytest",
        )
        db_session.add(domain)
        db_session.commit()
        db_session.refresh(domain)

        manager = DomainManager(db_session)

        def fake_cf_lookup(name: str):
            if name == domain.sajet_full_domain:
                return {
                    "found": True,
                    "records": [
                        {
                            "type": "CNAME",
                            "name": name,
                            "content": "tcs-sajet-tunnel.cfargotunnel.com",
                            "proxied": True,
                        }
                    ],
                }
            return {"found": False, "records": []}

        def fake_resolve(name: str, record_type: str):
            raise dns.resolver.NXDOMAIN

        monkeypatch.setattr(manager, "_verify_via_cloudflare_api", fake_cf_lookup)
        monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)

        result = asyncio.run(manager.verify_domain(domain.id))

        assert result["success"] is False
        assert result["status"] == "failed"
        db_session.refresh(domain)
        assert domain.verification_status == DomainVerificationStatus.failed
        assert domain.is_active is False

    def test_internal_sajet_domain_can_verify_via_cloudflare_api(
        self,
        db_session,
        sample_customer,
        monkeypatch,
    ):
        domain = CustomDomain(
            customer_id=sample_customer.id,
            external_domain="boletly.sajet.us",
            sajet_subdomain="boletly",
            verification_status=DomainVerificationStatus.pending,
            target_node_ip="localhost",
            target_port=8069,
            created_by="pytest",
        )
        db_session.add(domain)
        db_session.commit()
        db_session.refresh(domain)

        manager = DomainManager(db_session)

        def fake_cf_lookup(name: str):
            if name == domain.external_domain:
                return {
                    "found": True,
                    "records": [
                        {
                            "type": "CNAME",
                            "name": name,
                            "content": "tcs-sajet-tunnel.cfargotunnel.com",
                            "proxied": True,
                        }
                    ],
                }
            return {"found": False, "records": []}

        monkeypatch.setattr(manager, "_verify_via_cloudflare_api", fake_cf_lookup)

        result = asyncio.run(manager.verify_domain(domain.id))

        assert result["success"] is True
        assert result["status"] == "verified"
        db_session.refresh(domain)
        assert domain.verification_status == DomainVerificationStatus.verified
        assert domain.is_active is True
