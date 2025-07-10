from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


engine = create_async_engine('sqlite+aiosqlite:///books.db', echo=True)
new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session


class Base(DeclarativeBase):
    pass