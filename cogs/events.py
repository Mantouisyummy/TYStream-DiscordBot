import asyncio
from typing import Dict, Set, Optional

import aiohttp
import pytz

from disnake import Embed, Color, ButtonStyle, Webhook, ApplicationCommandInteraction, Guild
from disnake.utils import MISSING
from disnake.ui import Button
from disnake.ext import commands, tasks
from tystream import TwitchStreamData, AsyncYoutube, YoutubeStreamDataAPI, YoutubeStreamDataYTDLP

import Constants
from core.bot import Bot

from tystream.async_api import AsyncTwitch

from core.db import get_all_streamers, get_guild, upsert_message, get_message_id, get_action, get_webhook
from core.embeds import TwitchVODEmbed
from core.redis_utils import *

# streamers = ["hennie2001", "wildtamsuinese", "yoro1027"]  # need change

taipei_tz = pytz.timezone("Asia/Taipei")

notified_streams = set()


def replace_text(text, role: Optional[str] = None):
    if not role:
        return text

    replacements = {"{everyone}": "@everyone", "{here}": "@here", "{role}": role}

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


async def send_yt_webhook(data, guild: Guild, stream: YoutubeStreamDataAPI | YoutubeStreamDataYTDLP):

    print(stream)

    guild_id = guild.id

    if not data:
        return

    webhook_url = data.webhook_link
    webhook_avatar = data.webhook_avatar
    webhook_name = data.webhook_name

    embed = Embed(title=stream.title if isinstance(stream, YoutubeStreamDataAPI) else stream.fulltitle, colour=Color.red())
    embed.set_author(name=f"{stream.channelTitle} is live!", url=stream.url if isinstance(stream, YoutubeStreamDataAPI) else stream.webpage_url)
    embed.set_image(url=stream.thumbnails.medium.url if isinstance(stream, YoutubeStreamDataAPI) else stream.thumbnail)
    embed.add_field(
        name="Live start time",
        value=f"<t:{int(stream.LiveDetails.actualStartTime.astimezone(pytz.timezone('Asia/Taipei')).replace(tzinfo=None).timestamp() if isinstance(stream, YoutubeStreamDataAPI) else stream.timestamp)}:R>",
        inline=True,
    )
    embed.add_field(
        name="View count",
        value=(
            stream.LiveDetails.concurrentViewers or 0
            if isinstance(stream, YoutubeStreamDataAPI)
            else stream.concurrent_view_count
        ),
        inline=True,
    )
    embed.set_footer(text="This notice is issued by TYStream.", icon_url="https://i.imgur.com/g1bfpCW.png")

    role_mention = (
        guild.get_role(int(data.notification_role)).mention
        if data.notification_role and guild.get_role(int(data.notification_role))
        else ""
    )

    content = replace_text(data.content, role_mention) if data.content else role_mention or MISSING

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        message = await webhook.send(
            content=content,
            embed=embed,
            username=webhook_name,
            avatar_url=webhook_avatar,
            components=Button(label="Watch Live", style=ButtonStyle.link, url=stream.url if isinstance(stream, YoutubeStreamDataAPI) else stream.webpage_url),
            wait=True,
        )

        await upsert_message(guild_id, message.id, platform="youtube")


async def send_twitch_webhook(data, guild: Guild, stream: TwitchStreamData):
    guild_id = guild.id

    if not data:
        return

    webhook_url = data.webhook_link
    webhook_avatar = data.webhook_avatar
    webhook_name = data.webhook_name

    embed = Embed(title=stream.title, colour=Color.purple())
    embed.set_author(
        name=f"{stream.user.display_name} 正在直播！",
        url=f"https://www.twitch.tv/{stream.user.login}",
        icon_url=stream.user.profile_image_url,
    )
    embed.set_image(url=stream.thumbnail_url)
    embed.add_field(
        name="直播開始時間",
        value=f"<t:{int(stream.started_at.astimezone(pytz.timezone('Asia/Taipei')).replace(tzinfo=None).timestamp())}:R>",
        inline=True,
    )
    embed.add_field(name="遊戲", value=stream.game_name, inline=True)
    embed.add_field(name="觀看人數", value=stream.viewer_count, inline=True)
    embed.set_footer(text="此通知由 TYStream 發布", icon_url="https://i.imgur.com/g1bfpCW.png")

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        message = await webhook.send(
            content=replace_text(data.content, guild.get_role(int(data.notification_role)).mention),
            embed=embed,
            username=webhook_name,
            avatar_url=webhook_avatar,
            components=Button(
                label="觀看直播", style=ButtonStyle.link, url=f"https://www.twitch.tv/{stream.user.login}"
            ),
            wait=True,
        )

        await upsert_message(guild_id, message.id, platform="twitch")


class Events(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.notified_streams = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"Cog {self.__class__.__name__} has started")
        self.check_twitch_stream.start()
        self.check_youtube_stream.start()
        self.bot.logger.info("Stream check loop has started")

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message("❌ 你沒有權限執行這個指令！", ephemeral=True)
        else:
            embed = Embed(
                title="❌ 啊喔，出現了一個錯誤!", description=f"一個錯誤出現了:\n```{error}```", colour=Color.red()
            )

            self.bot.logger.error(f"An error occurred: {error}")

            return await inter.edit_original_response(embed=embed)

    @tasks.loop(seconds=10)
    async def check_youtube_stream(self):
        streamer_guilds_map: Dict[str, Set[int]] = {}

        for guild in self.bot.guilds:
            streamers = get_youtube_guild_streamers(guild.id)
            if not streamers:
                streamers = await get_all_streamers(guild.id, platform="youtube")
                cache_youtube_guild_streamers(guild.id, streamers)

            for streamer in streamers:
                check_and_clear_youtube_streamer(streamer)
                streamer_guilds_map.setdefault(streamer, set()).add(guild.id)

        all_streamers = list(streamer_guilds_map.keys())

        stream_status = {streamer: is_youtube_streamer_live(streamer) for streamer in all_streamers}

        streamers_to_check = [streamer for streamer, live in stream_status.items() if not live]

        if streamers_to_check:
            async with AsyncYoutube(Constants.YOUTUBE_API_KEY) as youtube:
                tasks_list = [
                    youtube.check_stream_live(
                        streamer.decode('utf-8') if isinstance(streamer, bytes) else streamer, use_yt_dlp=False
                    )
                    for streamer in streamers_to_check
                ]
                results = await asyncio.gather(*tasks_list)

                for streamer, is_live in zip(streamers_to_check, results):
                    stream_status[streamer] = is_live
                    if is_live:
                        cache_youtube_streamer_live(streamer)

        for streamer, is_live in stream_status.items():
            if is_live:
                for guild_id in streamer_guilds_map[streamer]:
                    if not mark_youtube_as_notified(guild_id, streamer):
                        data = await get_guild(guild_id, platform="youtube")
                        print(f"🔔 Guild {guild_id}: {streamer} 正在直播 (YouTube)！")
                        await send_yt_webhook(data, self.bot.get_guild(guild_id), is_live)
                        mark_youtube_as_notified(guild_id, streamer)
            else:
                for guild_id in streamer_guilds_map[streamer]:
                    if has_youtube_notified(guild_id, streamer):
                        action = await get_action(guild_id, platform="youtube")
                        message_id = await get_message_id(guild_id, platform="youtube")

                        webhook_url = await get_webhook(guild_id, platform="youtube")

                        webhook = Webhook.from_url(webhook_url, session=aiohttp.ClientSession())

                        if message_id:
                            match action:
                                case 0:
                                    await webhook.delete_message(message_id)
                                case 1:
                                    await webhook.edit_message(message_id, content=f"{streamer.decode('utf-8') if isinstance(streamer, bytes) else streamer} **已結束直播**")
                    else:
                        clear_youtube_notified_streamer(streamer)
                        self.bot.logger.log(21, f"{streamer.decode('utf-8') if isinstance(streamer, bytes) else streamer} not live. (Youtube)")

    @tasks.loop(seconds=3)
    async def check_twitch_stream(self):
        streamer_guilds_map: Dict[str, Set[int]] = {}

        for guild in self.bot.guilds:
            streamers = get_twitch_guild_streamers(guild.id)
            if not streamers:
                streamers = await get_all_streamers(guild.id, platform="twitch")
                cache_twitch_guild_streamers(guild.id, streamers)

            for streamer in streamers:
                check_and_clear_twitch_streamer(streamer)
                streamer_guilds_map.setdefault(streamer, set()).add(guild.id)

        all_streamers = list(streamer_guilds_map.keys())

        stream_status = {streamer: is_twitch_streamer_live(streamer) for streamer in all_streamers}

        streamers_to_check = [streamer for streamer, live in stream_status.items() if not live]

        print(streamers_to_check)

        if streamers_to_check:
            async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
                tasks_list = [twitch.check_stream_live(streamer.decode('utf-8') if isinstance(streamer, bytes) else streamer) for streamer in streamers_to_check]
                results = await asyncio.gather(*tasks_list)

                for streamer, is_live in zip(streamers_to_check, results):
                    stream_status[streamer] = is_live
                    if is_live:
                        cache_twitch_streamer_live(streamer)

        for streamer, is_live in stream_status.items():
            if is_live:
                for guild_id in streamer_guilds_map[streamer]:
                    if not has_twitch_notified(guild_id, streamer):
                        data = await get_guild(guild_id, platform="twitch")
                        print(f"🔔 Guild {guild_id}: {streamer} 正在直播 (Twitch)！")
                        await send_twitch_webhook(data, self.bot.get_guild(guild_id), is_live)
                        mark_twitch_as_notified(guild_id, streamer)
            else:
                for guild_id in streamer_guilds_map[streamer]:
                    streamer = streamer.decode('utf-8')
                    if has_twitch_notified(guild_id, streamer):
                        action = await get_action(guild_id, platform="twitch")
                        message_id = await get_message_id(guild_id, platform="twitch")

                        webhook_url = await get_webhook(guild_id, platform="twitch")

                        webhook = Webhook.from_url(webhook_url, session=aiohttp.ClientSession())

                        if message_id:
                            match action:
                                case 0:
                                    await webhook.delete_message(message_id)
                                case 1:
                                    vod = await twitch.get_stream_vod(streamer)
                                    if vod:
                                        embed = TwitchVODEmbed(vod)
                                        await webhook.edit_message(
                                            message_id,
                                            content=f"{streamer} **已結束直播**",
                                            embed=embed,
                                            components=Button(label="觀看VOD", style=ButtonStyle.link, url=vod.url),
                                        )
                        clear_twitch_notified_streamer(streamer)
                    else:
                        self.bot.logger.log(25, streamer + " not live. (Twitch)")


def setup(bot: Bot):
    bot.add_cog(Events(bot))
