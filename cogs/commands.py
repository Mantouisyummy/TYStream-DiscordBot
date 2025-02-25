import asyncio
import re


import Constants

from disnake import Embed, Colour, ApplicationCommandInteraction, Attachment, TextChannel, Role
from disnake.ext import commands

from core.bot import Bot
from core.db import (
    upsert_user,
    search_streamers,
    get_all_streamers,
    upsert_channel,
    delete_user,
    upsert_webhook,
    get_guild, upsert_notification_content_and_role, upsert_action,
)

from tystream import AsyncTwitch

from core.embeds import SuccessEmbed, RemoveEmbed

actions = {"刪除": 0, "更新訊息為 VOD": 1, "保留": 2}

async def extract_twitch_username(twitch_name_or_link: str) -> str:
    match = re.search(r'^https://www\.twitch\.tv/(.+)$', twitch_name_or_link)
    if match:
        return match.group(1).split("/")[-1]
    return twitch_name_or_link


class Commands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"Cog {self.__class__.__name__} has started")

    @commands.slash_command()
    async def twitch(self, inter):
        pass

    @commands.slash_command()
    async def youtube(self, inter):
        pass

    @commands.slash_command(name="ping", description="Pong")
    async def ping(self, inter: ApplicationCommandInteraction):
        embed = Embed(title="🏓 Pong!", description=f"{round(self.bot.latency * 1000)} ms", colour=Colour.random())
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="查看群組設定", description="查看機器人在群組內的設定")
    async def show_guild_settings(self, inter: ApplicationCommandInteraction):
        guild = await get_guild(inter.guild_id, platform="twitch")

        embed = Embed(title="📜 群組設定", colour=Colour.random())

        if not guild:
            embed.description = "尚未設定"
            embed.colour = Colour.red()
            await inter.response.send_message(embed=embed)
            return

        embed.add_field(
            name="直播通知頻道",
            value=inter.guild.get_channel(int(guild.channel_id)).mention if guild.channel_id else "無",
            inline=False,
        )

        embed.add_field(
            name="通知樣式",
            value=(
                f"名稱: {guild.webhook_name}\n頭像: [點我查看頭像]({guild.webhook_avatar})"
                if guild.webhook_name and guild.webhook_avatar
                else "無"
            ),
        )

        embed.add_field(
            name="通知身分組",
            value=inter.guild.get_role(int(guild.notification_role)).mention if guild.notification_role else "無",
        )

        embed.add_field(
            name="通知訊息",
            value=guild.content if guild.content else "無",
        )

        embed.add_field(
            name="直播結束時的動作",
            value=actions.get(guild.when_live_end, "保留"),
            inline=False,
        )

        embed.set_footer(text="ㄐ器人由 鰻頭(´・ω・) 製作", icon_url="https://i.imgur.com/noEDGCf.png")

        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="自訂通知樣式", description="設定直播通知傳送時的頭像和名稱")
    async def set_notification_style(
        self,
        inter: ApplicationCommandInteraction,
        name: str = commands.Param(name="名稱", description="通知時顯示的名稱", default=None),
        avatar: Attachment = commands.Param(name="頭像", description="通知時顯示的頭像 (上傳圖片檔案)", default=None),
    ):

        description_parts = []
        if name:
            await upsert_webhook(inter.guild.id, name=name, platform="twitch")
            description_parts.append(f"已將通知樣式的名稱設定為 `{name}`")
        if avatar:
            await upsert_webhook(inter.guild.id, avatar=avatar.url, platform="twitch")
            description_parts.append(f"已將通知樣式的頭像設定為：[點我]({avatar.url})")

        description_text = "、".join(description_parts) if description_parts else "沒有變更任何設定"

        embed = SuccessEmbed(title="🎨 設定成功", description=f"{description_text}")

        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="自訂通知訊息", description="設定直播通知傳送時的頭像和名稱")
    async def set_notification_content(
        self,
        inter: ApplicationCommandInteraction,
        role: Role = commands.Param(name="身分組", description="通知時要標記的身分組", default=None),
        content: str = commands.Param(name="訊息", description="通知時要傳送的訊息 (顯示在嵌入訊息上方)", default=None),
    ):

        await upsert_notification_content_and_role(inter.guild.id, role.id, content, platform="twitch")

        description_parts = []

        if role:
            description_parts.append(f"已將通知訊息標記的身分設定為 {role.mention}")
        if content:
            description_parts.append(f"已將通知樣式的訊息設定為：{content}")

        description_text = "\n".join(description_parts) if description_parts else "沒有變更任何設定"

        embed = SuccessEmbed(title="🎨 設定成功", description=f"{description_text}")

        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="設定直播通知頻道", description="將直播通知頻道設定為目前的頻道")
    @commands.has_guild_permissions(manage_channels=True)
    async def add_notification_channel(
        self,
        inter: ApplicationCommandInteraction,
        channel: TextChannel = commands.Param(name="頻道", description="直播頻道"),
    ):
        await upsert_channel(inter.guild.id, channel=channel.id, platform="twitch")

        webhooks = await channel.webhooks()

        if not any("直播通知" == w.name for w in webhooks):
            webhook = await channel.create_webhook(name="直播通知")
            await upsert_webhook(inter.guild_id, link=webhook.url, platform="twitch")

        embed = SuccessEmbed(title="🎉 新增成功", description=f"已將直播通知頻道設定為 {channel.mention}")

        await inter.response.send_message(embed=embed)

    # twitch

    @twitch.sub_command(name="新增實況主", description="將實況主新增至群組直播追蹤列表，並在其開播時發送提醒")
    @commands.has_guild_permissions(manage_guild=True)
    async def add_streamer(
        self,
        inter: ApplicationCommandInteraction,
        username: str = commands.Param(name="實況主頻道", description="Twitch 用戶名稱或連結"),
    ):
        await inter.response.defer()

        twitch_username = await extract_twitch_username(username)

        await upsert_user(inter.guild.id, twitch_username, platform="twitch")

        async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
            user = await twitch.get_user(twitch_username)

        embed = SuccessEmbed(
            title="🎉 新增成功", description=f"已新增 {user.display_name} 至群組直播追蹤列表", thumbnail=user.profile_image_url
        )

        await inter.edit_original_response(embed=embed)

    @twitch.sub_command(name="移除實況主", description="將實況主從群組直播追蹤列表中移除")
    @commands.has_guild_permissions(manage_guild=True)
    async def delete_streamer(
        self,
        inter: ApplicationCommandInteraction,
        username: str = commands.Param(
            name="實況主頻道",
            autocomplete=lambda inter, query: search_streamers(inter.guild.id, query, platform="twitch"),
            description="Twitch 用戶名稱或連結",
        ),
    ):
        await inter.response.defer()

        twitch_username = await extract_twitch_username(username)

        streamers = await get_all_streamers(inter.guild.id, platform="twitch")
        if twitch_username not in streamers:
            await inter.response.send_message(f"❌ `{twitch_username}` 不在追蹤列表內", ephemeral=True)
            return

        await delete_user(inter.guild.id, twitch_username, platform="twitch")

        async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
            user = await twitch.get_user(twitch_username)

        embed = RemoveEmbed(
            title="🗑️ 移除成功", description=f"已從群組直播追蹤列表中移除 {user.display_name}", thumbnail=user.profile_image_url
        )

        await inter.edit_original_response(embed=embed)

    @twitch.sub_command(name="查看實況主", description="查看群組直播追蹤列表中的所有實況主")
    async def list_streamers(self, inter: ApplicationCommandInteraction):
        await inter.response.defer()

        streamers = await get_all_streamers(inter.guild_id, platform="twitch")

        if not streamers:
            embed = RemoveEmbed(title="<:twitch:1343217893441011833> 目前追蹤列表 (Twitch)", description="無")
            await inter.edit_original_response(embed=embed)
            return

        async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
            users = await asyncio.gather(*(twitch.get_user(streamer) for streamer in streamers))

        description = "\n".join(f"[{user.display_name}](https://www.twitch.tv/{user.login})" for user in users)

        embed = SuccessEmbed(title="<:twitch:1343217893441011833> 目前追蹤列表 (Twitch)", description=description)

        await inter.edit_original_response(embed=embed)

    Actions = commands.option_enum({"刪除": 0, "更新訊息為 VOD": 1, "保留": 2})

    @twitch.sub_command(name="設定直播結束時的動作", description="可設定直播結束後，是否刪除通知訊息還是編輯通知訊息")
    @commands.has_guild_permissions(manage_guild=True)
    async def set_action_when_live_end(self, inter: ApplicationCommandInteraction, action: Actions):
        await upsert_action(inter.guild.id, action, platform="twitch")

        action_name = {v: k for k, v in actions.items()}[action]

        embed = SuccessEmbed(
            title="🎉 設定成功",
            description=f"已設定直播結束時的動作為：{action_name}",
        )

        await inter.response.send_message(embed=embed)

    # # youtube chinese version
    # @youtube.sub_command(name="新增頻道", description="將 YouTube 頻道新增至群組直播追蹤列表，並在其開播時發送提醒")
    # @commands.has_guild_permissions(manage_guild=True)
    # async def add_channel(
    #     self,
    #     inter: ApplicationCommandInteraction,
    #     channel: str = commands.Param(name="頻道", description="YouTube 頻道連結"),
    # ):
    #     await upsert_user(inter.guild.id, channel, platform="youtube")
    #
    #     embed = SuccessEmbed(title="🎉 新增成功", description=f"已新增 {channel} 至群組直播追蹤列表")
    #
    #     await inter.response.send_message(embed=embed)
    #
    # @youtube.sub_command(name="移除頻道", description="將 YouTube 頻道從群組直播追蹤列表中移除")
    # @commands.has_guild_permissions(manage_guild=True)
    # async def delete_channel(
    #     self,
    #     inter: ApplicationCommandInteraction,
    #     channel: str = commands.Param(
    #         name="頻道",
    #         autocomplete=lambda inter, query: search_streamers(inter.guild.id, query, platform="youtube"),
    #         description="YouTube 頻道連結",
    #     ),
    # ):
    #     streamers = get_all_streamers(inter.guild.id, platform="youtube")
    #     if channel not in streamers:
    #         await inter.response.send_message(f"❌ `{channel}` 不在追蹤列表內", ephemeral=True)
    #         return
    #
    #     await delete_user(inter.guild.id, channel, platform="youtube")
    #
    #     embed = RemoveEmbed(title="🗑️ 移除成功", description=f"已從群組直播追蹤列表中移除 {channel}")
    #
    #     await inter.response.send_message(embed=embed)
    #
    # @youtube.sub_command(name="查看頻道", description="查看群組直播追蹤列表中的所有頻道")
    # async def list_channels(self, inter: ApplicationCommandInteraction):
    #     streamers = await get_all_streamers(inter.guild_id, platform="youtube")
    #
    #     if not streamers:
    #         embed = RemoveEmbed(title="<:youtube:1343218062991560735> 目前追蹤列表 (Youtube)", description="無")
    #         await inter.response.send_message(embed=embed)
    #         return
    #
    #     description = "\n".join(f"[{streamer}](https://www.youtube.com/channel/{streamer})" for streamer in streamers)
    #
    #     embed = SuccessEmbed(title="<:youtube:1343218062991560735> 目前追蹤列表 (Youtube)", description=description)
    #
    #     await inter.response.send_message(embed=embed)

    # youtube
    @youtube.sub_command(name="add_channel", description="Add YouTube channels to your guild live tracking list and send alerts when they're on.")
    @commands.has_guild_permissions(manage_guild=True)
    async def add_channel(
        self,
        inter: ApplicationCommandInteraction,
        channel: str = commands.Param(name="channel", description="YouTube Channel Link"),
    ):
        await upsert_user(inter.guild.id, channel, platform="youtube")

        embed = SuccessEmbed(title="🎉 Success!", description=f"Added {channel} to the guild live tracking list")

        await inter.response.send_message(embed=embed)

    @youtube.sub_command(name="remove_channel", description="Remove YouTube channel from guild live tracking list")
    @commands.has_guild_permissions(manage_guild=True)
    async def delete_channel(
        self,
        inter: ApplicationCommandInteraction,
        channel: str = commands.Param(
            name="channel",
            autocomplete=lambda inter, query: search_streamers(inter.guild.id, query, platform="youtube"),
            description="YouTube Channel Link",
        ),
    ):
        streamers = await get_all_streamers(inter.guild.id, platform="youtube")
        if channel not in streamers:
            await inter.response.send_message(f"❌ `{channel}` no longer in the tracking list", ephemeral=True)
            return

        await delete_user(inter.guild.id, channel, platform="youtube")

        embed = RemoveEmbed(title="🗑️ Success!", description=f"Removed from group live tracking list {channel}")

        await inter.response.send_message(embed=embed)

    @youtube.sub_command(name="view_channels", description="View all channels in the group live tracking list")
    async def list_channels(self, inter: ApplicationCommandInteraction):
        streamers = await get_all_streamers(inter.guild_id, platform="youtube")

        if not streamers:
            embed = RemoveEmbed(title="<:youtube:1343218062991560735> Current Tracking List (Youtube)", description="None")
            await inter.response.send_message(embed=embed)
            return

        description = "\n".join(f"[{streamer}](https://www.youtube.com/channel/{streamer})" for streamer in streamers)

        embed = SuccessEmbed(title="<:youtube:1343218062991560735> Current Tracking List (Youtube)", description=description)

        await inter.response.send_message(embed=embed)

def setup(bot: Bot):
    bot.add_cog(Commands(bot))
