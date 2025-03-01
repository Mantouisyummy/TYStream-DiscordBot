from contextlib import asynccontextmanager

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from models.platform import TwitchGuilds, YouTubeGuilds
from core.base import Base

DATABASE_URL = "sqlite+aiosqlite:///tystream.db"
engine = create_async_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False})

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def async_session_scope():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

async def create_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_guild(guild_id: int, platform: str) -> TwitchGuilds | YouTubeGuilds:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        return result.scalar()

async def upsert_notification_content_and_role(guild_id: int, role_id: int, content: str, platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            if role_id:
                guild.notification_role = role_id
            if content:
                guild.content = content
        else:
            guild = model(
                id=guild_id,
                notification_role=role_id if role_id else None,
                content=content if content else None
            )

        session.add(guild)



async def upsert_message(guild_id: int, message_id: int, platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            guild.message_id = message_id
        else:
            guild = model(id=guild_id, message_id=message_id)

        session.add(guild)

async def upsert_user(guild_id: int, streamer: str, platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild is None:
            guild = model(id=guild_id, streamers=[])

        if not isinstance(guild.streamers, list):
            guild.streamers = []

        if streamer not in guild.streamers:
            guild.streamers.append(streamer)
            flag_modified(guild, "streamers")

        session.add(guild)

async def upsert_action(guild_id: int, action: int, platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            guild.when_live_end = action
        else:
            guild = model(id=guild_id, when_live_end=action)

        session.add(guild)
        await session.commit()

async def upsert_channel(guild_id: int, channel: Optional[int], platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            guild.channel_id = channel
        else:
            guild = model(id=guild_id, channel_id=channel)

        session.add(guild)


async def get_channel(guild_id: int, platform: str) -> Optional[int]:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()
        return guild.channel_id if guild else None

async def get_message_id(guild_id: int, platform: str) -> Optional[int]:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()
        return guild.message_id if guild else None

async def get_action(guild_id: int, platform: str) -> int:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()
        return guild.when_live_end if guild else 3

async def get_webhook(guild_id: int, platform: str) -> Optional[str]:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()
        return guild.webhook_link if guild else None

async def upsert_webhook(
    guild_id: int,
    platform: str,
    link: Optional[str] = None,
    name: Optional[str] = None,
    avatar: Optional[str] = None
):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            if name:
                guild.webhook_name = name
            elif avatar:
                guild.webhook_avatar = avatar
            elif link:
                guild.webhook_link = link
        else:
            if link:
                guild = model(id=guild_id, webhook_link=link)
                session.add(guild)
            else:
                raise ValueError("初始化时必须提供 `link`")

        await session.commit()


async def delete_user(guild_id: int, streamer: str, platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            if guild.streamers is None:
                guild.streamers = []

            if streamer in guild.streamers:
                guild.streamers.remove(streamer)

                flag_modified(guild, "streamers")

                session.add(guild)
                await session.commit()

async def delete_message(guild_id: int, platform: str):
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if guild:
            guild.message_id = None

        session.add(guild)

async def get_all_streamers(guild_id: int, platform: str) -> List[str]:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()
        return guild.streamers if guild and isinstance(guild.streamers, list) else []


async def search_streamers(guild_id: int, query: str, platform: str) -> List[str]:
    async with async_session_scope() as session:
        model = TwitchGuilds if platform == "twitch" else YouTubeGuilds
        stmt = select(model).where(model.id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar()

        if not guild or not isinstance(guild.streamers, list):
            return []

        return [s for s in guild.streamers if query.lower() in s.lower()]
