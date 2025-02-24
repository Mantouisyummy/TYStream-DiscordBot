import re
from typing import Optional

import pytz
from disnake import Embed, Colour
from tystream import TwitchVODData


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


def convert_duration(duration):
    units = {'d': '天', 'h': '小時', 'm': '分鐘', 's': '秒'}
    matches = re.findall(r'(\d+)([dhms])', duration)

    return " ".join(f"{num} {units[unit]}" for num, unit in matches)


class TwitchVODEmbed(Embed):
    def __init__(self, vod: TwitchVODData):
        super().__init__(title=vod.title, colour=Colour.purple())

        self.set_thumbnail(url=vod.thumbnail_url)

        self.add_field(name="觀看人數", value=vod.view_count, inline=True)
        self.add_field(name="長度", value=convert_duration(vod.duration), inline=True)

        self.set_footer(text=f"ㄐ器人由 鰻頭(´・ω・) 製作 • {vod.published_at.astimezone(pytz.timezone("Asia/Taipei")).replace(tzinfo=None)} 結束直播", icon_url="https://i.imgur.com/noEDGCf.png")