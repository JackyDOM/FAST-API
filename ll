import asyncio
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import UUID

from ..app.core.config import settings
from ..app.core.db.database import AsyncSession, async_engine, local_session
from ..app.core.services.spr_service import encrypt_password
from ..app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_first_user(session: AsyncSession) -> None:
    try:
        # name = settings.ADMIN_NAME
        email = settings.ADMIN_EMAIL
        username = settings.ADMIN_USERNAME
        # hashed_password = get_password_hash(settings.ADMIN_PASSWORD)

        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            metadata = MetaData()
            user_table = Table(
                "user",
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
                Column("name", String(30), nullable=False),
                Column("username", String(20), nullable=False, unique=True, index=True),
                Column("email", String(50), nullable=False, unique=True, index=True),
                Column("hashed_password", String, nullable=False),
                Column("profile_image_url", String, default="https://profileimageurl.com"),
                Column(
                    "uuid",
                    UUID(as_uuid=True),
                    primary_key=True,
                    default=uuid.uuid4,
                    unique=True,
                ),
                Column(
                    "created_at",
                    DateTime(timezone=True),
                    default=lambda: datetime.now(UTC),
                    nullable=False,
                ),
                Column("updated_at", DateTime),
                Column("deleted_at", DateTime),
                Column("is_deleted", Boolean, default=False, index=True),
                Column("is_superuser", Boolean, default=False),
                Column("tier_id", Integer, ForeignKey("tier.id"), index=True),
                Column("gazetteer_code", String(10), default=""),
            )

            # ------------- ca user -------------
            CA_NAME = "មន្ត្រី"
            CA_EMAIL = "gs_commune@gmail.com"
            CA_USERNAME = "gs_commune"
            CA_PASSWORD = "123456"

            # ------------- cc user -------------
            # CC_NAME = "មេឃុំ"
            # CC_EMAIL = "0301012@gmail.com"
            # CC_USERNAME = "0301012"
            # CC_PASSWORD = "123456"

            # ------------- gazetteer user -------------
            GAZETTEER_CODE = "010201"

            ca_data = {
                "name": CA_NAME,
                "email": CA_EMAIL,
                "username": CA_USERNAME,
                "hashed_password": encrypt_password(CA_PASSWORD),
                "is_superuser": True,
                "gazetteer_code": GAZETTEER_CODE,
            }

            # cc_data = {
            #     "name": CC_NAME,
            #     "email": CC_EMAIL,
            #     "username": CC_USERNAME,
            #     "hashed_password": encrypt_password(CC_PASSWORD),
            #     "is_superuser": True,
            #     "gazetteer_code": GAZETTEER_CODE,
            # }

            ca_stmt = insert(user_table).values(ca_data)
            # cc_stmt = insert(user_table).values(cc_data)

            async with async_engine.connect() as conn:
                await conn.execute(ca_stmt)
                # await conn.execute(cc_stmt)
                await conn.commit()

            logger.info(f"Admin user {username} created successfully.")

        else:
            logger.info(f"Admin user {username} already exists.")

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")


async def main():
    async with local_session() as session:
        await create_first_user(session)


if __name__ == "__main__":
    asyncio.run(main())



================

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import UUID

from ..app.core.config import settings
from ..app.core.db.database import AsyncSession, async_engine, local_session
from ..app.core.services.spr_service import encrypt_password
from ..app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_first_user(session: AsyncSession) -> None:
    try:
        # name = settings.ADMIN_NAME
        email = settings.ADMIN_EMAIL
        username = settings.ADMIN_USERNAME
        # hashed_password = get_password_hash(settings.ADMIN_PASSWORD)

        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            metadata = MetaData()
            user_table = Table(
                "user",
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
                Column("name", String(30), nullable=False),
                Column("username", String(20), nullable=False, unique=True, index=True),
                Column("email", String(50), nullable=False, unique=True, index=True),
                Column("hashed_password", String, nullable=False),
                Column("profile_image_url", String, default="https://profileimageurl.com"),
                Column(
                    "uuid",
                    UUID(as_uuid=True),
                    primary_key=True,
                    default=uuid.uuid4,
                    unique=True,
                ),
                Column(
                    "created_at",
                    DateTime(timezone=True),
                    default=lambda: datetime.now(UTC),
                    nullable=False,
                ),
                Column("updated_at", DateTime),
                Column("deleted_at", DateTime),
                Column("is_deleted", Boolean, default=False, index=True),
                Column("is_superuser", Boolean, default=False),
                Column("tier_id", Integer, ForeignKey("tier.id"), index=True),
                Column("gazetteer_code", String(10), default=""),
            )

            # ------------- ca user -------------
            CA_NAME = "មន្ត្រី"
            CA_EMAIL = "gs_commune@gmail.com"
            CA_USERNAME = "gs_commune"
            CA_PASSWORD = "123456"

            # ------------- cc user -------------
            # CC_NAME = "មេឃុំ"
            # CC_EMAIL = "0301012@gmail.com"
            # CC_USERNAME = "0301012"
            # CC_PASSWORD = "123456"

            # ------------- gazetteer user -------------
            GAZETTEER_CODE = "010201"

            ca_data = {
                "name": CA_NAME,
                "email": CA_EMAIL,
                "username": CA_USERNAME,
                "hashed_password": encrypt_password(CA_PASSWORD),
                "is_superuser": True,
                "gazetteer_code": GAZETTEER_CODE,
            }

            # cc_data = {
            #     "name": CC_NAME,
            #     "email": CC_EMAIL,
            #     "username": CC_USERNAME,
            #     "hashed_password": encrypt_password(CC_PASSWORD),
            #     "is_superuser": True,
            #     "gazetteer_code": GAZETTEER_CODE,
            # }

            ca_stmt = insert(user_table).values(ca_data)
            # cc_stmt = insert(user_table).values(cc_data)

            # extra 5 users
            # extra_commune_users = []

            # for i in range(1, 6):
            #     extra_commune_users.append(
            #         {
            #             "name": f"មន្ត្រី{i}",
            #             "email": f"gs_commune{i}@gmail.com",
            #             "username": f"gs_commune{i}",
            #             "hashed_password": encrypt_password(CA_PASSWORD),
            #             "is_superuser": True,
            #             "gazetteer_code": GAZETTEER_CODE,
            #         }
            #     )


            async with async_engine.connect() as conn:
                await conn.execute(ca_stmt)
                # await conn.execute(cc_stmt)

                # insert extra 5 users
                # for user_data in extra_commune_users:
                #     stmt = insert(user_table).values(user_data)
                #     await conn.execute(stmt)

                    
                await conn.commit()

            logger.info(f"Admin user {username} created successfully.")

        else:
            logger.info(f"Admin user {username} already exists.")

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")


async def main():
    async with local_session() as session:
        await create_first_user(session)


if __name__ == "__main__":
    asyncio.run(main())
