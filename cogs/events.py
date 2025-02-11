from disnake.ext import commands
from core.bot import Bot


class Events(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"Cog {self.__class__.__name__} has started")


def setup(bot: Bot):
    bot.add_cog(Events(bot))