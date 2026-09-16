"""Tests for the plan-v2.0 services: founders, disputes, QA, logistics.
All run on an in-memory SQLite database with the shared Base metadata."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import services.dispute_resolution.models  # noqa: F401  (register tables)
import services.logistics.models  # noqa: F401
import services.quality_assurance.models  # noqa: F401
import services.marketplace.models  # noqa: F401
import services.marketplace.models.marketplace_founder  # noqa: F401
from database.base import Base
from services.dispute_resolution.service import DisputeService
from services.logistics.service import LogisticsService
from services.marketplace.models.marketplace_founder import MarketplaceFounder
from services.quality_assurance.service import QualityService


@pytest.fixture()
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    yield session
    session.close()
    engine.dispose()


# --- founders ---------------------------------------------------------------

def test_founder_create_and_dict(db_session):
    f = MarketplaceFounder(marketplace_id='mkt-1', user_id='u-1', role='founder',
                           equity_share=60.0, contribution_type='land')
    db_session.add(f)
    db_session.commit()
    d = f.to_dict()
    assert d['role'] == 'founder' and d['equity_share'] == 60.0


def test_founder_equity_bounds(db_session):
    with pytest.raises(Exception):
        db_session.add(MarketplaceFounder(marketplace_id='m', user_id='u',
                                          equity_share=150.0))
        db_session.commit()


def test_founder_unique_pair(db_session):
    db_session.add(MarketplaceFounder(marketplace_id='m', user_id='u'))
    db_session.commit()
    db_session.add(MarketplaceFounder(marketplace_id='m', user_id='u'))
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()


# --- disputes ----------------------------------------------------------------

def test_dispute_lifecycle(db_session):
    svc = DisputeService(db_session)
    d = svc.create(order_id='o-1', complainant_id='buyer-1', category='quality',
                   description='Product arrived damaged and quality was below promise.')
    assert d.status == 'open'
    svc.add_event(d.id, 'evidence', 'buyer-1', 'photos attached')
    d2 = svc.get(d.id)
    assert d2.status == 'under_review'
    resolved = svc.resolve(d.id, 'mediator-1', 'Partial refund issued to buyer.')
    assert resolved.status == 'resolved' and resolved.resolution
    assert len(svc.events(d.id)) >= 3


def test_dispute_validation(db_session):
    svc = DisputeService(db_session)
    with pytest.raises(ValueError):
        svc.create(order_id='o-2', complainant_id='b', category='nonsense', description='x' * 20)
    with pytest.raises(LookupError):
        svc.resolve('missing-id', 'm', 'r')


# --- quality -----------------------------------------------------------------

def test_qa_pass_with_certificate(db_session):
    svc = QualityService(db_session)
    insp = svc.create_inspection(product_id='p-1', inspection_type='harvest')
    out = svc.record_result(insp.id, 90.0, 'excellent quality')
    assert out['inspection'].status == 'passed'
    assert out['certificate_id'] is not None


def test_qa_fail_no_certificate(db_session):
    svc = QualityService(db_session)
    insp = svc.create_inspection(product_id='p-2', inspection_type='packaging')
    out = svc.record_result(insp.id, 40.0)
    assert out['inspection'].status == 'failed'
    assert out['certificate_id'] is None
    with pytest.raises(ValueError):
        svc.record_result(insp.id, 150.0)


# --- logistics ----------------------------------------------------------------

def test_logistics_happy_path(db_session):
    svc = LogisticsService(db_session)
    sh = svc.create(order_id='o-9', carrier='tipax', origin='Golestan', destination='Tehran')
    assert sh.status == 'pending'
    svc.update_status(sh.id, 'picked_up', 'courier-1')
    svc.update_status(sh.id, 'in_transit', 'courier-1')
    sh2 = svc.update_status(sh.id, 'delivered', 'courier-1')
    assert sh2.status == 'delivered'
    assert len(svc.events(sh.id)) == 4  # created + 3 transitions


def test_logistics_illegal_transition(db_session):
    svc = LogisticsService(db_session)
    sh = svc.create(order_id='o-10')
    with pytest.raises(ValueError):
        svc.update_status(sh.id, 'delivered', 'x')  # pending -> delivered is illegal
