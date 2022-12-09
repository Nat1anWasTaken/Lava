from disnake.ext.commands import Cog


class SlashCommands(Cog):
    pass


def setup(bot):
    bot.add_cog(SlashCommands(bot))
