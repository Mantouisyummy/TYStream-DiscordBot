import re
import time
import pytz

from typing import Optional
from datetime import datetime

from disnake import Embed, Colour
from tystream import TwitchVODData, TwitchStreamData

from core.utils import convert_duration


class SuccessEmbed(Embed):
    def __init__(self, title: str, description: str, thumbnail: Optional[str] = None, **kwargs):
        super().__init__(title=title, description=description, colour=Colour.green(), **kwargs)

        if thumbnail:
            self.set_thumbnail(url=thumbnail)

        self.set_footer(text="ㄐ器人由 鰻頭(´・ω・) 製作", icon_url="https://i.imgur.com/noEDGCf.png")

class RemoveEmbed(Embed):
    def __init__(self, title: str, description: str, thumbnail: Optional[str] = None, **kwargs):
        super().__init__(title=title, description=description, colour=Colour.green(), **kwargs)

        if thumbnail:
            self.set_thumbnail(url=thumbnail)

        self.set_footer(text="ㄐ器人由 鰻頭(´・ω・) 製作", icon_url="https://i.imgur.com/noEDGCf.png")


class TwitchStreamEmbed(Embed):
    def __init__(self, stream: TwitchStreamData):
        super().__init__(title=stream.title, colour=Colour.purple())

        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz).strftime("%H:%M")

        self.set_author(
            name=f"{stream.user.display_name} 正在直播！",
            url=f"https://www.twitch.tv/{stream.user.login}",
            icon_url=stream.user.profile_image_url,
        )
        self.set_image(url=f"{stream.thumbnail_url}?t={int(time.time())}")
        self.add_field(
            name="直播開始時間",
            value=f"<t:{int(stream.started_at.astimezone(pytz.timezone('Asia/Taipei')).replace(tzinfo=None).timestamp())}:R>",
            inline=True,
        )
        self.add_field(name="遊戲", value=stream.game_name, inline=True)
        self.add_field(name="觀看人數", value=stream.viewer_count, inline=True)

        self.set_footer(
            text=f"此通知由 TYStream 發布 • ㄐ器人由 鰻頭(´・ω・) 製作 • 最後編輯時間 {current_time}",
            icon_url="https://i.imgur.com/g1bfpCW.png"
        )


class TwitchVODEmbed(Embed):
    def __init__(self, vod: TwitchVODData):
        super().__init__(title=vod.title, colour=Colour.purple())

        self.set_thumbnail(url=vod.thumbnail_url)

        self.add_field(name="觀看人數", value=vod.view_count, inline=True)
        self.add_field(name="時長", value=convert_duration(vod.duration), inline=True)
        self.add_field(
            name="直播結束時間",
            value=f"<t:{int(vod.published_at.astimezone(pytz.timezone('Asia/Taipei')).replace(tzinfo=None).timestamp())}:R>",
            inline=True,
        )

        self.set_footer(
            text=f"此通知由 TYStream 發布 • ㄐ器人由 鰻頭(´・ω・) 製作",
            icon_url="https://i.imgur.com/g1bfpCW.png"
        )