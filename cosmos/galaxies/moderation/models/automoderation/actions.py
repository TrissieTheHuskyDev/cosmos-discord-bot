from ..moderation.moderation import ModerationAction

from ..moderation import actions


class AutoModerationActions(object):

    def __init__(self, trigger):
        self._trigger = trigger

    @property
    def warning(self):
        try:
            return getattr(self._trigger.profile.plugin.data.triggers_warning, self._trigger.name)
        except AttributeError:
            return f"You are being warned for violating {self._trigger.name}."

    @property
    def embed(self):
        return self._trigger.profile.plugin.bot.theme.embeds.one_line.primary

    @staticmethod
    async def delete(message=None, **_):
        await message.delete()

    async def warn(self, *, message=None, **_):
        if message:
            await message.channel.send(
                message.author.mention, embed=self.embed(self.warning), delete_after=4)
            await ModerationAction(
                self._trigger.profile, message.author, message.guild.me, actions.Warned(True), self.warning
            ).dispatch(f"⚠    You were warned in {self._trigger.profile.guild.name}.")

    async def mute(self, *, member, **kwargs):
        pass

    async def kick(self, *, member, **kwargs):
        pass

    async def ban(self, *, member, **kwargs):
        pass
