from disnake import Embed, Colour, ApplicationCommandInteraction
from disnake.ext import commands

from core.bot import Bot


class Commands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"Cog {self.__class__.__name__} has started")

    @commands.slash_command(name="ping", description="Pong")
    async def ping(self, inter: ApplicationCommandInteraction):
        embed = Embed(title="🏓 Pong!", description=f"{round(self.bot.latency * 1000)} ms", colour=Colour.random())
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="新增實況主", description="將實況主新增至群組直播追蹤列表，並在其開播時發送提醒")
    async def add_streamer(self, inter: ApplicationCommandInteraction):
        pass

    @commands.slash_command(name="移除實況主", description="將實況主從群組直播追蹤列表中移除")
    async def delete_streamer(self, inter: ApplicationCommandInteraction):
        pass

def setup(bot: Bot):
    bot.add_cog(Commands(bot))