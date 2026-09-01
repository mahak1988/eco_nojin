import structlog

logger = structlog.get_logger()
import os
"""Create sample data for testing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid

from database.config import SessionLocal, init_db
from database.models import EcoTransaction, EcoWallet, Farm, Product, SatelliteAnalysis, ScenarioRun, SoilAnalysis
from database.models import User


def create_test_data():
    logger.info("=" * 80)
    logger.info("🌱 Creating Test Data")
    logger.info("=" * 80)
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            logger.info("  ⚠️  Test data already exists. Skipping.")
            return
        user = User(
            email="demo@econojin.org",
            full_name="Demo Farmer",
            hashed_password = os.getenv("PASSWORD", ""),
            role="farmer",
            language="fa",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"  ✅ User: {user.email}")
        farm = Farm(
            name="Green Valley Farm",
            owner_id=user.id,
            latitude=35.6892,
            longitude=51.3890,
            elevation_m=1200,
            area_hectares=15.5,
            soil_type="loam",
            climate_zone="semi-arid",
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)
        logger.info(f"  ✅ Farm: {farm.name}")
        soil = SoilAnalysis(
            farm_id=farm.id,
            user_id=user.id,
            ph=6.8,
            organic_matter=2.5,
            nitrogen=45,
            phosphorus=28,
            potassium=180,
            clay=25,
            silt=45,
            sand=30,
            texture="loam",
            ph_status="neutral",
            organic_matter_rating="moderate",
            health_score=72.5,
            recommendations=["Add compost", "Use cover crops"],
        )
        db.add(soil)
        sat = SatelliteAnalysis(
            farm_id=farm.id,
            user_id=user.id,
            latitude=35.6892,
            longitude=51.3890,
            ndvi=0.65,
            evi=0.52,
            savi=0.48,
            ndwi=0.15,
            nbr=0.72,
            satellite="Sentinel-2",
        )
        db.add(sat)
        for sc, tc, pc, risk in [
            ("ssp126", 1.8, -5, 0.35),
            ("ssp245", 2.7, -10, 0.55),
            ("ssp370", 3.6, -15, 0.72),
            ("ssp585", 4.4, -20, 0.85),
        ]:
            db.add(
                ScenarioRun(
                    farm_id=farm.id,
                    user_id=user.id,
                    baseline_temp=18.5,
                    baseline_precip=380,
                    scenario=sc,
                    target_year=2050,
                    projected_temp=18.5 + tc,
                    projected_precip=380 * (1 + pc / 100),
                    temp_change=tc,
                    precip_change_percent=pc,
                    drought_risk_index=risk,
                    impact_assessment={"yield": "decrease" if tc > 2 else "stable"},
                )
            )
        wallet = EcoWallet(user_id=user.id, balance=250.0, total_earned=350.0, total_redeemed=100.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        for cat, amt, tx in [("tree_planting", 50, "earn"), ("consultation", 20, "redeem")]:
            db.add(
                EcoTransaction(
                    transaction_id=str(uuid.uuid4()),
                    wallet_id=wallet.id,
                    amount=amt,
                    transaction_type=tx,
                    category=cat,
                    description=f"{tx}: {cat}",
                    balance_after=wallet.balance,
                )
            )
        for n, c, p in [("Organic Wheat", "grain", 15.5), ("Saffron", "spice", 450)]:
            db.add(
                Product(
                    name=n, category=c, price=p, quantity=100, producer_id=user.id, is_organic=True
                )
            )
        db.commit()
        logger.info("  ✅ All test data created!")
    except Exception as e:
        db.rollback()
        logger.error(f"  ❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
