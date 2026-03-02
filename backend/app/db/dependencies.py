from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .session import get_async_session


async def get_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[AsyncSession, None]:
    yield session
