"""Seed test data for local development."""

import asyncio
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.agency import Agency
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

DEMO_AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

SEED_AGENCIES = [
    Agency(
        id=DEMO_AGENCY_ID,
        name="Bay Area Elite Homecare",
        slug="bay-area-elite",
        is_active=True,
        email="info@bayareaelitehomecare.com",
    ),
]

SEED_USERS = [
    User(
        email="superadmin@test.com",
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        agency_id=None,
    ),
    User(
        email="admin@test.com",
        first_name="Agency",
        last_name="Admin",
        role=UserRole.AGENCY_ADMIN,
        agency_id=DEMO_AGENCY_ID,
    ),
    User(
        email="manager1@test.com",
        first_name="Care",
        last_name="Manager",
        role=UserRole.CARE_MANAGER,
        agency_id=DEMO_AGENCY_ID,
    ),
    User(
        email="caregiver1@test.com",
        first_name="Jane",
        last_name="Nurse",
        role=UserRole.CAREGIVER,
        agency_id=DEMO_AGENCY_ID,
    ),
    User(
        email="caregiver2@test.com",
        first_name="John",
        last_name="Aide",
        role=UserRole.CAREGIVER,
        agency_id=DEMO_AGENCY_ID,
    ),
    User(
        email="family1@test.com",
        first_name="Mary",
        last_name="Relative",
        role=UserRole.FAMILY,
        agency_id=DEMO_AGENCY_ID,
    ),
    User(
        email="family2@test.com",
        first_name="Bob",
        last_name="Relative",
        role=UserRole.FAMILY,
        agency_id=DEMO_AGENCY_ID,
    ),
]


async def seed() -> None:
    """Seed the database with test data. Idempotent — skips existing records.

    Sets `app.current_tenant_id = ''` on the seed session so the post-0001
    `tenant_isolation` policy on `users` (and on `email_events`) admits the
    cross-tenant inserts the seed performs. The post-0008 dual-axis policies
    coalesce the GUC for us; the post-0001 policy does not, so we set it
    explicitly. Empty string = "no tenant context" = staff/super-admin path.
    """
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await session.execute(text("SET app.current_tenant_id = ''"))
        for agency in SEED_AGENCIES:
            existing = await session.execute(
                text("SELECT id FROM agencies WHERE slug = :slug"),
                {"slug": agency.slug},
            )
            if existing.first() is None:
                session.add(agency)
                logger.info("Created agency: %s", agency.name)
            else:
                logger.info("Agency exists: %s", agency.name)

        await session.commit()

        for user in SEED_USERS:
            existing = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user.email},
            )
            if existing.first() is None:
                session.add(user)
                logger.info("Created user: %s (%s)", user.email, user.role.value)
            else:
                logger.info("User exists: %s", user.email)

        await session.commit()

    await engine.dispose()
    logger.info("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
