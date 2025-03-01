import json
from logging import Logger

import aiohttp
from disnake.ext.commands import InteractionBot as OriginalBot

from core.db import create_table


class Bot(OriginalBot):
    def __init__(self, logger: Logger, **kwargs):
        super().__init__(**kwargs)

        self.logger = logger

    async def on_ready(self):
        await create_table()
        self.logger.info("The bot is ready! Logged in as %s" % self.user)