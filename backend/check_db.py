import asyncio

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.connect() as conn:
        print(
            "DATABASE:",
            (
                await conn.execute(
                    text("SELECT current_database(), current_user")
                )
            ).fetchone(),
        )

        print(
            "DOCUMENTS:",
            (
                await conn.execute(
                    text(
                        "SELECT table_schema, table_name "
                        "FROM information_schema.tables "
                        "WHERE table_name='documents'"
                    )
                )
            ).fetchall(),
        )

        print(
            "TABLE COUNT:",
            (
                await conn.execute(
                    text(
                        "SELECT count(*) "
                        "FROM information_schema.tables "
                        "WHERE table_schema='public'"
                    )
                )
            ).scalar(),
        )


asyncio.run(main())