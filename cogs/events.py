import asyncio
from typing import Dict, Set

import aiohttp
import pytz

from disnake import Embed, Color, ButtonStyle, Webhook, ApplicationCommandInteraction, Guild
from disnake.ui import Button
from disnake.ext import commands, tasks
from tystream import TwitchStreamData

import Constants
from core.bot import Bot

from tystream.async_api import AsyncTwitch

from core.db import get_all_streamers, get_guild, upsert_message, get_message_id, get_action, get_webhook
from core.embeds import TwitchVODEmbed
from core.redis_utils import (
    get_guild_streamers,
    cache_guild_streamers,
    is_streamer_live,
    cache_streamer_live,
    has_notified,
    mark_as_notified,
    clear_notified_streamer,
)

# streamers = ["hennie2001", "wildtamsuinese", "yoro1027"]  # need change

taipei_tz = pytz.timezone("Asia/Taipei")

notified_streams = set()

def replace_text(text, role: str):
    replacements = {
        "{everyone}": "@everyone",
        "{here}": "@here",
        "{role}": role,
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

async def send_webhook(data, guild: Guild,stream: TwitchStreamData):
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
    embed.add_field(name="遊戲", value=stream.game_name, inline=True)
    embed.add_field(name="觀看人數", value=stream.viewer_count, inline=True)
    embed.set_footer(
        text=f"ㄐ器人由 鰻頭(´・ω・) 製作 • {stream.started_at.astimezone(pytz.timezone("Asia/Taipei")).replace(tzinfo=None)} 開始直播",
        icon_url="https://i.imgur.com/noEDGCf.png",
    )

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
        self.bot.logger.info("Stream check loop has started")

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message("❌ 你沒有權限執行這個指令！", ephemeral=True)
        else:
            embed = Embed(
                title="❌ 啊喔，出現了一個錯誤!", description=f"一個錯誤出現了:\n```{error}```", colour=Color.red()
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

    # @tasks.loop(seconds=3)
    # async def check_yt_stream(self):
    #     streamer_guilds_map: Dict[str, Set[int]] = {}
    #
    #     for guild in self.bot.guilds:
    #         streamers = get_guild_streamers(guild.id)
    #         if not streamers:
    #             streamers = await get_all_streamers(guild.id)
    #             cache_guild_streamers(guild.id, streamers)
    #
    #         for streamer in streamers:
    #             if streamer not in streamer_guilds_map:
    #                 streamer_guilds_map[streamer] = set()
    #             streamer_guilds_map[streamer].add(guild.id)
    #
    #     all_streamers = list(streamer_guilds_map.keys())
    #
    #     async with AsyncYoutube() as twitch:
    #         stream_status = {}
    #         for streamer in all_streamers:
    #             if is_streamer_live(streamer):
    #                 stream_status[streamer] = True
    #             else:
    #                 stream_status[streamer] = await twitch.check_stream_live(streamer.decode("utf-8"))
    #                 if stream_status[streamer]:
    #                     cache_streamer_live(streamer)
    #
    #         for streamer, stream in stream_status.items():
    #             if stream:
    #                 for guild_id in streamer_guilds_map[streamer]:
    #                     if not has_notified(guild_id, streamer):
    #                         print(f"🔔 Guild {guild_id}: {streamer} 正在直播 (Youtube) ！")
    #                         await send_webhook(guild_id, streamer, stream)
    #                         mark_as_notified(guild_id, streamer)
    #             else:
    #                 clear_notified_streamer(streamer)

    @tasks.loop(seconds=3)
    async def check_twitch_stream(self):
        streamer_guilds_map: Dict[str, Set[int]] = {}

        for guild in self.bot.guilds:
            streamers = get_guild_streamers(guild.id)
            if not streamers:
                streamers = await get_all_streamers(guild.id, platform="twitch")
                cache_guild_streamers(guild.id, streamers)

            for streamer in streamers:
                streamer_guilds_map.setdefault(streamer, set()).add(guild.id)

        all_streamers = list(streamer_guilds_map.keys())

        stream_status = {streamer: is_streamer_live(streamer) for streamer in all_streamers}

        streamers_to_check = [streamer for streamer, live in stream_status.items() if not live]

        if streamers_to_check:
            async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
                tasks_list = [twitch.check_stream_live(streamer.decode('utf-8')) for streamer in streamers_to_check]
                results = await asyncio.gather(*tasks_list)

                for streamer, is_live in zip(streamers_to_check, results):
                    stream_status[streamer] = is_live
                    if is_live:
                        cache_streamer_live(streamer)

        for streamer, is_live in stream_status.items():
            if is_live:
                for guild_id in streamer_guilds_map[streamer]:
                    if not has_notified(guild_id, streamer):
                        data = await get_guild(guild_id, platform="twitch")
                        print(f"🔔 Guild {guild_id}: {streamer} 正在直播 (Twitch)！")
                        await send_webhook(data, self.bot.get_guild(guild_id), is_live)
                        mark_as_notified(guild_id, streamer)
            else:
                for guild_id in streamer_guilds_map[streamer]:
                    streamer = streamer.decode('utf-8')
                    if has_notified(guild_id, streamer):
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
                        clear_notified_streamer(streamer)
                    else:
                        self.bot.logger.log(21, streamer + " not live.")


def setup(bot: Bot):
    bot.add_cog(Events(bot))
