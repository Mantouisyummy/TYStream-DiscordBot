import asyncio
import re


import Constants

from disnake import Embed, Colour, ApplicationCommandInteraction, Attachment, TextChannel, Role, Localized
from disnake.ext import commands

from core.bot import Bot
from core.db import (
    upsert_user,
    search_streamers,
    get_all_streamers,
    upsert_channel,
    delete_user,
    upsert_webhook,
    get_guild,
    upsert_notification_content_and_role,
    upsert_action,
)

from tystream import AsyncTwitch

from core.embeds import SuccessEmbed, RemoveEmbed
from core.redis_utils import remove_twitch_guild_streamers, remove_youtube_guild_streamers

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

    # @commands.slash_command()
    # async def youtube(self, inter):
    #     pass

    @commands.slash_command(name=Localized("help", data={"zh-TW": "指令幫助"}), description="顯示機器人的指令教學")
    async def help(self, inter: ApplicationCommandInteraction):
        embed = Embed(
            title="指令教學",
            description=(
                "## 🎉 歡迎來到指令教學！\n"
                "請依照以下步驟來設定本機器人：\n\n"
                "### 🔔 設定頻道\n"
                "📌 點選 </twitch set_notification_channel:1343141104580694027>，然後選擇你想發送通知的頻道。\n\n"
                "### ✨ 設定通知身分和訊息 (可選)\n"
                "⚙️ 點選 </custom_notification_message:1344817673019593028>，選擇你想設定的通知身分組和訊息。\n\n"
                "📢 訊息可以輸入以下的替換字元來自訂想顯示的內容：\n"
                "* 🔹 **{everyone}** → Tag 所有人\n"
                "* 🔹 **{here}** → Tag 當前在線的成員\n"
                "* 🔹 **{role}** → Tag 設定的通知身分組\n\n"
                "### 🎭 自訂通知帳號的頭像和名稱 (可選)\n"
                "🖼️ 點選 </custom_notififcation_styles:1343141104580694028>，可自訂傳送直播通知的帳號頭像和名稱 (頭像需先下載到本地)。\n\n"
                "### 🏁 設定直播結束後的動作 (預設為保留)\n"
                "🚀 點選 </twitch set_actions_after_stream_ends:1343141104580694027>，依照出現的選項選擇即可。\n\n"
                "### 🎥 新增想追蹤的 Twitch 實況主\n"
                "🌟 點選 </twitch add_streamer:1343141104580694027>，輸入實況主的連結，例如：\n"
                "🔗 [範例頻道](https://www.twitch.tv/mantouoao)\n"
            ),
            colour=Colour.random(),
        )

        embed.set_footer(text="ㄐ器人由 鰻頭(´・ω・) 製作", icon_url="https://i.imgur.com/noEDGCf.png")

        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="ping", description="Pong")
    async def ping(self, inter: ApplicationCommandInteraction):
        embed = Embed(title="🏓 Pong!", description=f"{round(self.bot.latency * 1000)} ms", colour=Colour.random())
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name=Localized("view_setting", data={"zh-TW": "查看群組設定"}), description="查看機器人在群組內的設定")
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

        embed.add_field(name="通知訊息", value=guild.content if guild.content else "無")

        embed.add_field(name="直播結束時的動作", value=actions.get(guild.when_live_end, "保留"), inline=False)

        embed.set_footer(text="ㄐ器人由 鰻頭(´・ω・) 製作", icon_url="https://i.imgur.com/noEDGCf.png")

        await inter.response.send_message(embed=embed)

    @commands.slash_command(name=Localized("custom_notififcation_styles", data={"zh-TW": "自訂通知樣式"}), description="設定通知樣式的名稱和頭貼")
    async def set_notification_style(
        self,
        inter: ApplicationCommandInteraction,
        name: str = commands.Param(name="名稱", description="通知帳號的名稱", default=None),
        avatar: Attachment = commands.Param(
            name="頭像", description="通知帳號的頭像 (使用上傳圖片檔案的方式)", default=None
        ),
    ):
        await inter.response.defer(ephemeral=True)

        if avatar and avatar.content_type not in ["image/png", "image/jpeg"]:
            embed = Embed(title="❌ 錯誤", description="頭像必須是 PNG 或 JPEG 格式", colour=Colour.red())
            embed.set_footer(text="ㄐ器人由 鰻頭(´・ω・) 製作", icon_url="https://i.imgur.com/noEDGCf.png")
            await inter.edit_original_response(embed=embed)
            return

        description_parts = []
        if name:
            await upsert_webhook(inter.guild.id, name=name, platform="twitch")
            description_parts.append(f"通知樣式名稱已設定為： `{name}`")
        if avatar:
            await upsert_webhook(inter.guild.id, avatar=avatar.url, platform="twitch")
            description_parts.append(f"通知樣式頭像已設定為： [點我]({avatar.url})")

        description_text = "、".join(description_parts) if description_parts else "沒有變更任何設定"

        embed = SuccessEmbed(title="🎨 成功設定!", description=f"{description_text}")

        await inter.edit_original_response(embed=embed)

    @commands.slash_command(
        name=Localized("custom_notification_message", data={"zh-TW": "自訂通知訊息"}),
        description="設定直播通知傳送時的頭像和名稱"
    )
    async def set_notification_content(
            self,
            inter: ApplicationCommandInteraction,
            role: Role = commands.Param(name="身分組", description="通知時要標記的身分組", default=None),
            content: str = commands.Param(name="訊息", description="通知時要傳送的訊息 (顯示在嵌入訊息上方)",
                                          default=None),
    ):
        role_id = role.id if role else None
        content_text = content if content else None

        if role_id or content_text:
            await upsert_notification_content_and_role(inter.guild.id, role_id, content_text, platform="twitch")

        description_parts = []

        if role:
            description_parts.append(f"已將通知訊息標記的身分設定為 {role.mention}")
        if content:
            description_parts.append(f"已將通知樣式的訊息設定為：{content}")

        description_text = "\n".join(description_parts) if description_parts else "沒有變更任何設定"

        embed = SuccessEmbed(title="🎨 設定成功", description=f"{description_text}")

        await inter.response.send_message(embed=embed)

    @twitch.sub_command(name=Localized("set_notification_channel", data={"zh-TW": "設定通知頻道"}), description="設定開始直播時傳送通知的頻道")
    @commands.has_guild_permissions(manage_channels=True)
    async def add_twitch_notification_channel(
        self,
        inter: ApplicationCommandInteraction,
        channel: TextChannel = commands.Param(name="頻道", description="直播通知頻道"),
    ):
        await upsert_channel(inter.guild.id, channel=channel.id, platform="twitch")

        webhooks = await channel.webhooks()

        webhook = next((w for w in webhooks if w.name == "TYStream直播通知"), None)

        if webhook is None:
            webhook = await channel.create_webhook(name="TYStream直播通知")

        await upsert_webhook(inter.guild.id, link=webhook.url, platform="twitch")

        embed = SuccessEmbed(title="🎉 新增成功!", description=f"Twitch 的直播通知頻道已設定為 {channel.mention}")
        await inter.response.send_message(embed=embed)

    # twitch

    @twitch.sub_command(name=Localized("add_streamer", data={"zh-TW": "新增實況主"}), description="將實況主新增至群組直播追蹤列表，並在其開播時發送提醒")
    @commands.has_guild_permissions(manage_guild=True)
    async def add_streamer(
        self,
        inter: ApplicationCommandInteraction,
        link: str = commands.Param(name="實況主頻道", description="Twitch 連結"),
    ):
        await inter.response.defer(ephemeral=True)

        streamers = await get_all_streamers(inter.guild.id, platform="twitch")

        twitch_username = await extract_twitch_username(link)

        if twitch_username in streamers:
            await inter.edit_original_response(f"❌ `{twitch_username}` 已在追蹤列表內")
            return

        await upsert_user(inter.guild.id, twitch_username, platform="twitch")

        async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
            user = await twitch.get_user(twitch_username)

        embed = SuccessEmbed(
            title="🎉 新增成功",
            description=f"已新增 {user.display_name} 至群組直播追蹤列表",
            thumbnail=user.profile_image_url,
        )

        await inter.edit_original_response(embed=embed)

    @twitch.sub_command(name=Localized("remove_streamer", data={"zh-TW": "移除實況主"}), description="將實況主從群組直播追蹤列表中移除")
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
        await inter.response.defer(ephemeral=True)

        twitch_username = await extract_twitch_username(username)

        remove = remove_twitch_guild_streamers(inter.guild.id, twitch_username)

        streamers = await get_all_streamers(inter.guild.id, platform="twitch")
        if twitch_username not in streamers:
            await inter.edit_original_response(f"❌ `{twitch_username}` 不在追蹤列表內")
            return

        if remove:
            await delete_user(inter.guild.id, twitch_username, platform="twitch")

            async with AsyncTwitch(Constants.TWITCH_CLIENT_ID, Constants.TWITCH_CLIENT_SECRET) as twitch:
                user = await twitch.get_user(twitch_username)

            embed = RemoveEmbed(
                title="🗑️ 移除成功",
                description=f"已從群組直播追蹤列表中移除 {user.display_name}",
                thumbnail=user.profile_image_url,
            )

            return await inter.edit_original_response(embed=embed)

    @twitch.sub_command(name=Localized("view_streamer", data={"zh-TW": "查看實況主"}), description="查看群組直播追蹤列表中的所有實況主")
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

    @twitch.sub_command(name=Localized("set_actions_after_stream_ends", data={"zh-TW": "設定直播結束後的動作"}), description="可設定直播結束後，是否刪除通知訊息還是編輯通知訊息")
    @commands.has_guild_permissions(manage_guild=True)
    async def set_action_when_live_end(self, inter: ApplicationCommandInteraction, action: Actions):
        await upsert_action(inter.guild.id, action, platform="twitch")

        action_name = {v: k for k, v in actions.items()}[action]

        embed = SuccessEmbed(title="🎉 設定成功", description=f"已設定直播結束時的動作為：{action_name}")

        await inter.response.send_message(embed=embed)

    # youtube
    # @youtube.sub_command(name="新增頻道", description="將 YouTube 頻道新增至群組直播追蹤列表，並在其開播時發送提醒")
    # @commands.has_guild_permissions(manage_guild=True)
    # async def add_channel(
    #     self,
    #     inter: ApplicationCommandInteraction,
    #     channel: str = commands.Param(name="channel", description="YouTube Channel Link"),
    # ):
    #
    #     await inter.response.defer(ephemeral=True)
    #
    #     streamers = await get_all_streamers(inter.guild.id, platform="youtube")
    #
    #     match = re.search(r'@([\w_-]+)', channel)
    #
    #     channel = match.group(1) if match else channel
    #
    #     if channel in streamers:
    #         await inter.edit_original_response(f"❌ `{channel}` Already in the tracking list")
    #         return
    #
    #     if not match:
    #         return await inter.edit_original_response(embed=Embed(title="❌ 錯誤", description="無效的連結", colour=Colour.red()))
    #
    #     await upsert_user(inter.guild.id, match.group(1), platform="youtube")
    #
    #     embed = SuccessEmbed(title="🎉 Success!", description=f"Added {channel} to the guild live tracking list")
    #
    #     await inter.edit_original_response(embed=embed)
    #
    # @youtube.sub_command(name="移除頻道", description="將 YouTube 頻道從群組直播追蹤列表中移除")
    # @commands.has_guild_permissions(manage_guild=True)
    # async def delete_channel(
    #     self,
    #     inter: ApplicationCommandInteraction,
    #     channel: str = commands.Param(
    #         name="channel",
    #         autocomplete=lambda inter, query: search_streamers(inter.guild.id, query, platform="youtube"),
    #         description="YouTube Channel Link",
    #     ),
    # ):
    #
    #     await inter.response.defer(ephemeral=True)
    #
    #     streamers = await get_all_streamers(inter.guild.id, platform="youtube")
    #
    #     if channel not in streamers:
    #         await inter.edit_original_response(f"❌ `{channel}` no longer in the tracking list")
    #         return
    #
    #     remove_youtube_guild_streamers(inter.guild.id, channel)
    #
    #     await delete_user(inter.guild.id, channel, platform="youtube")
    #
    #     embed = RemoveEmbed(title="🗑️ Success!", description=f"Removed from group live tracking list {channel}")
    #
    #     await inter.edit_original_response(embed=embed)

    #
    # @youtube.sub_command(name="查看頻道", description="查看群組直播追蹤列表中的所有頻道")
    # async def list_channels(self, inter: ApplicationCommandInteraction):
    #     await inter.response.defer()
    #
    #     streamers = await get_all_streamers(inter.guild_id, platform="youtube")
    #
    #     if not streamers:
    #         embed = RemoveEmbed(title="<:youtube:1343218062991560735> Current Tracking List (Youtube)", description="None")
    #         await inter.edit_original_response(embed=embed)
    #         return
    #
    #     description = "\n".join(f"[{streamer}](https://www.youtube.com/channel/{streamer})" for streamer in streamers)
    #
    #     embed = SuccessEmbed(title="<:youtube:1343218062991560735> Current Tracking List (Youtube)", description=description)
    #
    #     await inter.edit_original_response(embed=embed)
    #
    # @youtube.sub_command(name="設定通知頻道", description="設定開始直播時傳送通知的頻道")
    # @commands.has_guild_permissions(manage_channels=True)
    # async def add_yt_notification_channel(
    #     self,
    #     inter: ApplicationCommandInteraction,
    #     channel: TextChannel = commands.Param(name="頻道", description="直播通知頻道"),
    # ):
    #     await upsert_channel(inter.guild.id, channel=channel.id, platform="youtube")
    #
    #     webhooks = await channel.webhooks()
    #
    #     webhook = next((w for w in webhooks if w.name == "TYStream直播通知"), None)
    #
    #     if webhook is None:
    #         webhook = await channel.create_webhook(name="TYStream直播通知")
    #
    #     await upsert_webhook(inter.guild.id, link=webhook.url, platform="youtube")
    #
    #     embed = SuccessEmbed(
    #         title="🎉 新增成功!",
    #         description=f"Youtube 的直播通知頻道已設定為 {channel.mention}"
    #     )
    #     await inter.response.send_message(embed=embed)


def setup(bot: Bot):
    bot.add_cog(Commands(bot))
