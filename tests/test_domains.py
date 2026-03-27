"""
Tests for custom domain verification flows.
"""
import asyncio
import pytest

import dns.resolver
from fastapi import HTTPException

from app.models.database import CustomDomain, DomainVerificationStatus, Plan, Subscription, SubscriptionStatus
from app.routes.domains import _check_domain_limit
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


class TestDomainCreation:
    def test_create_domain_uses_customer_sajet_subdomain(
        self,
        db_session,
        sample_customer,
    ):
        manager = DomainManager(db_session)

        result = manager.create_domain(
            external_domain="latazacuriosa.com",
            customer_id=sample_customer.id,
            created_by="pytest",
        )

        assert result["success"] is True
        assert result["domain"]["sajet_subdomain"] == sample_customer.subdomain
        assert result["domain"]["sajet_full_domain"] == f"{sample_customer.subdomain}.sajet.us"
        assert result["instructions"]["record_value"] == f"{sample_customer.subdomain}.sajet.us"

    def test_same_tenant_can_have_multiple_external_domains(
        self,
        db_session,
        sample_customer,
    ):
        manager = DomainManager(db_session)

        result_one = manager.create_domain(
            external_domain="techeels.com",
            customer_id=sample_customer.id,
            created_by="pytest",
        )
        result_two = manager.create_domain(
            external_domain="techeels.do",
            customer_id=sample_customer.id,
            created_by="pytest",
        )

        assert result_one["success"] is True
        assert result_two["success"] is True
        assert result_one["domain"]["sajet_subdomain"] == sample_customer.subdomain
        assert result_two["domain"]["sajet_subdomain"] == sample_customer.subdomain


class TestDomainPlanLimits:
    def test_plan_limit_counts_pending_domains_too(
        self,
        db_session,
        sample_customer,
    ):
        plan = Plan(
            name="pro",
            display_name="Pro",
            max_domains=1,
            is_active=True,
        )
        db_session.add(plan)
        db_session.commit()

        subscription = Subscription(
            customer_id=sample_customer.id,
            plan_name="pro",
            status=SubscriptionStatus.active,
        )
        db_session.add(subscription)
        db_session.commit()

        domain = CustomDomain(
            customer_id=sample_customer.id,
            external_domain="techeels.com",
            sajet_subdomain=sample_customer.subdomain,
            verification_status=DomainVerificationStatus.pending,
            is_active=False,
            target_node_ip="localhost",
            target_port=8069,
            created_by="pytest",
        )
        db_session.add(domain)
        db_session.commit()

        with pytest.raises(HTTPException) as exc:
            _check_domain_limit(db_session, sample_customer.id)

        assert exc.value.status_code == 403
