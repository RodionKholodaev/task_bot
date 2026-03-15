from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import DB_URL
from models import Base

# инициализация async БД
# DB_URL должен быть вида sqlite+aiosqlite:///tasks.db (или другой async-драйвер)
engine = create_async_engine(DB_URL, echo=False, future=True) #type: ignore
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """Создание таблиц при запуске"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session() -> AsyncSession:
    """Получение асинхронной сессии БД"""
    return AsyncSessionLocal()


