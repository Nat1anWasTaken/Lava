from disnake import Member, TextChannel
from disnake.ext.commands import CommandError
from disnake.utils import get

from core.classes import Bot
from library.classes import LavalinkVoiceClient


async def ensure_voice(bot: Bot, member: Member, channel: TextChannel,
                       should_connect: bool = True) -> LavalinkVoiceClient:
    """
    This check ensures that the bot and command author are in the same voice channel.

    :member: The member to check for.
    :should_connect: Whether the bot should connect to the voice channel if it isn't already connected.
    """
    player = bot.lavalink.player_manager.create(member.guild.id)
    # Create returns a player if one exists, otherwise creates.
    # This line is important because it ensures that a player always exists for a guild.

    # Most people might consider this a waste of resources for guilds that aren't playing, but this is
    # the easiest and simplest way of ensuring players are created.

    if not member.voice or not member.voice.channel:
        # Our cog_command_error handler catches this and sends it to the voice channel.
        # Exceptions allow us to "short-circuit" command invocation via checks so the
        # execution state of the command goes no further.
        raise CommandError('請先加入一個語音頻道')

    v_client = get(bot.voice_clients, guild=member.guild)

    if not v_client:
        if not should_connect:
            raise CommandError('機器人沒有連接到一個語音頻道')

        permissions = member.voice.channel.permissions_for(member.guild.get_member(bot.user.id))

        if not permissions.connect or not permissions.speak:  # Check user limit too?
            raise CommandError('我需要 `連接` 和 `說話` 權限')

        player.store('channel', channel.id)

        # noinspection PyTypeChecker
        return await member.voice.channel.connect(cls=LavalinkVoiceClient)

    else:
        if v_client.channel.id != member.voice.channel.id:
            raise CommandError(f'你必須要和我在同一個語音頻道 (<#{v_client.channel.id}>)裡面')
