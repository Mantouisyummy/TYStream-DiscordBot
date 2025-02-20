from disnake.ext import commands, tasks
from core.bot import Bot

from tystream import Twitch

twitch = Twitch()

class Events(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"Cog {self.__class__.__name__} has started")

    @tasks.loop(seconds=3)
    async def check_stream(self):
        stream = await twitch.check_stream_live("")

        if stream:
            self.bot.logger.info(f"Stream: {stream}")

def setup(bot: Bot):
    bot.add_cog(Events(bot))