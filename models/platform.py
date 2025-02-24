from sqlalchemy import Column, BigInteger, String, Integer
from sqlalchemy.dialects.sqlite import JSON
from core.base import Base

class GuildMixin:
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    streamers = Column(JSON, nullable=False, default=lambda: [])
    content = Column(String, nullable=True)
    channel_id = Column(BigInteger, nullable=True)
    message_id = Column(BigInteger, nullable=True)
    webhook_link = Column(String, nullable=True)
    webhook_name = Column(String, nullable=True, default="直播通知")
    webhook_avatar = Column(String, nullable=True, default="https://i.imgur.com/g1bfpCW.png")
    notification_role = Column(BigInteger, nullable=True)
    when_live_end = Column(Integer, nullable=False, default=3)

class TwitchGuilds(Base, GuildMixin):
    __tablename__ = "twitch_guilds"

class YouTubeGuilds(Base, GuildMixin):
    __tablename__ = "youtube_guilds"