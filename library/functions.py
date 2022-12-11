from typing import Union

from disnake import Interaction, Message, Thread, TextChannel, Embed, NotFound
from disnake.abc import GuildChannel
from disnake.utils import get
from lavalink import DefaultPlayer

from core.classes import Bot
from library.classes import LavalinkVoiceClient
from library.errors import UserNotInVoice, MissingVoicePermissions, BotNotInVoice, UserInDifferentChannel


async def ensure_voice(interaction: Interaction, should_connect: bool) -> LavalinkVoiceClient:
    """
    This check ensures that the bot and command author are in the same voice channel.

    :param interaction: The interaction that triggered the command.
    :param should_connect: Whether the bot should connect to the voice channel if it isn't already connected.
    """
    player = interaction.bot.lavalink.player_manager.create(interaction.author.guild.id)

    if not interaction.author.voice or not interaction.author.voice.channel:
        raise UserNotInVoice('Please join a voice channel first')

    v_client = get(interaction.bot.voice_clients, guild=interaction.author.guild)

    if not v_client:
        if not should_connect:
            raise BotNotInVoice('Bot is not in a voice channel.')

        permissions = interaction.author.voice.channel.permissions_for(
            interaction.author.guild.get_member(interaction.bot.user.id)
        )

        if not permissions.connect or not permissions.speak:  # Check user limit too?
            raise MissingVoicePermissions('Connect and Speak permissions is required in order to play music')

        player.store('channel', interaction.channel.id)

        # noinspection PyTypeChecker
        return await interaction.author.voice.channel.connect(cls=LavalinkVoiceClient)

    else:
        if v_client.channel.id != interaction.author.voice.channel.id:
            raise UserInDifferentChannel(
                v_client.channel, "User must be in the same voice channel as the bot"
            )


async def update_display(bot: Bot, player: DefaultPlayer, new_message: Message = None):
    """
    Update the display of the current song.

    Note: If new message is provided, Old message will be deleted after 5 seconds

    :param bot: The bot instance.
    :param player: The player instance.
    :param new_message: The new message to update the display with, None to use the old message.
    """
    # noinspection PyTypeChecker
    channel: Union[GuildChannel, TextChannel, Thread] = bot.get_channel(int(player.fetch('channel')))

    try:
        message: Message = await channel.fetch_message(int(player.fetch('message')))
    except (TypeError, NotFound):  # Message not found
        if not new_message:
            raise NotFound('Message not found, no message to update with.')

    if new_message:
        try:
            await message.delete(delay=5)
        except (AttributeError, UnboundLocalError):
            pass

        message = new_message

    await message.edit(embed=generate_display_embed(player))

    player.store('message', message.id)


def generate_display_embed(player: DefaultPlayer) -> Embed:
    # TODO: Complete this embed
    embed = Embed(title='正在播放', colour=0x1ED760, description=player.current.title)

    embed.add_field(name='點播者', value=f"<@{player.current.requester}>")

    return embed
