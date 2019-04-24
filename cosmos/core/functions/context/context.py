from discord.ext import commands

from .functions import *


class CosmosContext(commands.Context):

    @property
    def emotes(self):
        return self.bot.emotes

    @property
    def embeds(self):
        return self.bot.theme.embeds

    @property
    def embed_line(self):
        return self.bot.theme.embeds.one_line.primary

    async def send_line(self, *args, **kwargs):
        return await self.send(embed=self.bot.theme.embeds.one_line.primary(*args, **kwargs))

    async def trigger_loading(self, timeout=10):
        async with Loading(self):
            await asyncio.sleep(timeout)

    def loading(self):
        return Loading(self)

    def get_paginator(self, *args, **kwargs):
        return BasePaginator(self, *args, **kwargs)

    def get_field_paginator(self, *args, **kwargs):
        return FieldPaginator(self, *args, **kwargs)

    def get_menu(self, *args, **kwargs):
        return BaseMenu(self, *args, **kwargs)

    def get_field_menu(self, *args, **kwargs):
        return FieldMenu(self, *args, **kwargs)

    async def confirm(self, message=None):
        menu = ConfirmMenu(self, message)
        await menu.wait_for_confirmation()
        return menu.confirmed