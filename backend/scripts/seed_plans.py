"""
Seed script to create default subscription plans.

Usage:
    python -m scripts.seed_plans
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config.env import env
from src.core.database.models.plan import Plan, PlanType


async def seed_plans():
    """Create default subscription plans."""
    
    # Create async engine
    engine = create_async_engine(env.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Check if plans already exist
            from sqlalchemy import select
            result = await session.execute(select(Plan))
            existing_plans = result.scalars().all()
            
            if existing_plans:
                print(f"✓ Plans already exist ({len(existing_plans)} plans found)")
                for plan in existing_plans:
                    print(f"  - {plan.code}: {plan.name}")
                return
            
            # Define plans
            plans = [
                {
                    "code": "FREE",
                    "name": "Free Plan",
                    "description": "Basic free plan for testing the service",
                    "plan_type": PlanType.FREE.value,
                    "plan_cost": 0,
                    "plan_discount": 0,
                    "monthly_minutes": 30,
                    "monthly_usage_limit": 10,
                },
                {
                    "code": "BASIC",
                    "name": "Basic Plan",
                    "description": "Affordable plan for individual users",
                    "plan_type": PlanType.BASIC.value,
                    "plan_cost": 9_99,  # $9.99
                    "plan_discount": 0,
                    "monthly_minutes": 180,  # 3 hours
                    "monthly_usage_limit": 50,
                },
                {
                    "code": "PREMIUM",
                    "name": "Premium Plan",
                    "description": "Advanced plan for power users",
                    "plan_type": PlanType.PREMIUM.value,
                    "plan_cost": 29_99,  # $29.99
                    "plan_discount": 0,
                    "monthly_minutes": 600,  # 10 hours
                    "monthly_usage_limit": 200,
                },
                {
                    "code": "ENTERPRISE",
                    "name": "Enterprise Plan",
                    "description": "Unlimited plan for businesses",
                    "plan_type": PlanType.ENTERPRISE.value,
                    "plan_cost": 99_99,  # $99.99
                    "plan_discount": 0,
                    "monthly_minutes": 3600,  # 60 hours
                    "monthly_usage_limit": 1000,
                },
            ]
            
            # Create plans
            for plan_data in plans:
                plan = Plan(**plan_data)
                session.add(plan)
                print(f"✓ Created plan: {plan_data['code']} - {plan_data['name']}")
            
            await session.commit()
            print(f"\n✓ Successfully seeded {len(plans)} plans!")
            
        except Exception as e:
            print(f"✗ Error seeding plans: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("=== Seeding Subscription Plans ===\n")
    asyncio.run(seed_plans())

