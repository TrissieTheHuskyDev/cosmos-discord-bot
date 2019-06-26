from .models.automoderation import triggers

from .. import Cog

from discord.ext import commands


class ActionConvertor(commands.Converter):

    def convert(self, ctx, argument):
        argument = argument.lower().replace(" ", "_")
        try:
            return getattr(triggers.AutoModerationActions, argument).__name__
        except AttributeError:
            raise commands.BadArgument(f"❌    Action {argument} isn't supported yet.")


class TriggerConvertor(commands.Converter):

    def convert(self, ctx, argument):
        _ = argument.lower().replace(" ", "_")
        if _ not in triggers.__triggers__:
            raise commands.BadArgument(f"❌    Trigger or violation {argument} isn't supported yet.")
        return _


class AutoModeration(Cog):

    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    async def cog_check(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            raise commands.MissingPermissions(["administrator"])
        return True

    @Cog.listener()
    async def on_message(self, message):
        guild_profile = await self.bot.guild_cache.get_profile(message.guild.id)

        trigger = guild_profile.auto_moderation.triggers.get("banned_words")
        if trigger and set(message.content.lower().split()) & trigger.banned_words:
            await trigger.dispatch(message.author)

    @Cog.group(name="triggers", aliases=["trigger", "violation", "violations"], invoke_without_command=True)
    async def triggers(self, ctx):
        guild_profile = await ctx.fetch_guild_profile()
        embed = ctx.embed_line(f"Active auto moderation triggers or violations", ctx.guild.icon_url)
        if guild_profile.auto_moderation.triggers:
            embed.description = ", ".join([trigger.title for trigger in guild_profile.auto_moderation.triggers])
        else:
            embed.description = "❌    No auto moderation triggers or violations has been set yet."
        await ctx.send(embed=embed)

    @triggers.command(name="create", aliases=["set", "add"])
    async def create_trigger(self, ctx, trigger: TriggerConvertor, *actions: ActionConvertor):
        pass

    @create_trigger.error
    async def create_trigger_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send_line(str(error))

    @triggers.command(name="remove", aliases=["delete"])
    async def remove_trigger(self, ctx):
        pass

    # @Cog.group(name="banword", aliases=["bannedwords", "banwords"], invoke_without_command=True)
    # async def ban_word(self, ctx, word=None):
    #     guild_profile = await ctx.fetch_guild_profile()
    #     if not word:
    #         embed = ctx.embed_line(f"List of banned words in {ctx.guild.name}", ctx.guild.icon_url)
    #         if guild_profile.auto_moderation.banned_words:
    #             embed.description = ", ".join(guild_profile.banned_words)
    #         else:
    #             embed.description = "No words banned yet."
    #         return await ctx.send(embed=embed)
    #     await guild_profile.auto_moderation.ban_word(word.lower())
    #     await ctx.send_line(f"✅    {word} has been added to list of banned words.")
    #
    # @ban_word.command(name="clear", aliases=["clean", "purge"])
    # async def clear_banned_words(self, ctx):
    #     guild_profile = await ctx.fetch_guild_profile()
    #     await guild_profile.clear_banned_words()
    #     await ctx.send_line(f"✅    List of banned words in this server has been cleared.")