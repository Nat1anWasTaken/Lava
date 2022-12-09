from disnake.ext.commands import Cog


class MessageCommands(Cog):
    pass


def setup(bot):
    bot.add_cog(MessageCommands(bot))
