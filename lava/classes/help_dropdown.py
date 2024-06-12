from disnake import SelectOption, MessageInteraction, Locale, Embed, Colour

from disnake.ui import StringSelect, View

from disnake.ext.commands import InvokableSlashCommand

from lava.bot import Bot


class HelpDropdown(StringSelect):
    def __init__(self, bot: Bot):
        options = [SelectOption(label=name, value=name) for name in bot.all_slash_commands.keys()]
        super().__init__(placeholder="選擇一個指令", custom_id="help_select", options=options)
    
    async def callback(self, interaction: MessageInteraction):
        await interaction.response.send_message(embed=self.__generate_help_embed(interaction.bot.all_slash_commands[interaction.data.values[0]], interaction.locale), ephemeral=True)
    
    def __generate_help_embed(self, command: InvokableSlashCommand, locale: Locale) -> Embed:
        name = command.body.name
        description = command.body.description_localizations.data[locale.value]
        command_options = command.body.options

        embed = Embed(
            title=f"{name} Command",
            description=description,
            colour=Colour.random()
        )

        return embed

class DropDownView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown(bot))