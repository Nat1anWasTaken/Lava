from disnake.ext.commands import Cog


class Commands(Cog):
    pass


def setup(bot):
    bot.add_cog(Commands(bot))
