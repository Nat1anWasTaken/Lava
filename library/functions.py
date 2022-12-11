import asyncio
from typing import Union

from disnake import Interaction, Message, Thread, TextChannel, Embed, NotFound, Colour
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


async def update_display(bot: Bot, player: DefaultPlayer, new_message: Message = None, delay: int = 0):
    """
    Update the display of the current song.

    Note: If new message is provided, Old message will be deleted after 5 seconds

    :param bot: The bot instance.
    :param player: The player instance.
    :param new_message: The new message to update the display with, None to use the old message.
    :param delay: The delay in seconds before updating the display.
    """
    await asyncio.sleep(delay)

    # noinspection PyTypeChecker
    channel: Union[GuildChannel, TextChannel, Thread] = bot.get_channel(int(player.fetch('channel')))

    try:
        message: Message = await channel.fetch_message(int(player.fetch('message')))
    except (TypeError, NotFound):  # Message not found
        if not new_message:
            raise ValueError("No message found or provided to update the display with")

    if new_message:
        try:
            await message.delete()
        except (AttributeError, UnboundLocalError):
            pass

        message = new_message

    await message.edit(embed=generate_display_embed(player))

    player.store('message', message.id)


def generate_display_embed(player: DefaultPlayer) -> Embed:
    # TODO: Complete this embed
    embed = Embed()

    if player.is_playing and player.is_playing:
        embed.set_author(name='播放中', icon_url="https://cdn.discordapp.com/emojis/987643956403781692.webp")

        embed.colour = Colour.green()

    elif player.is_connected and player.is_playing and player.paused:
        embed.set_author(name='已暫停', icon_url="https://cdn.discordapp.com/emojis/987661771609358366.webp")

        embed.colour = Colour.orange()

    elif not player.is_connected:
        embed.set_author(name='已斷線', icon_url="https://cdn.discordapp.com/emojis/987646268094439488.webp")

        embed.colour = Colour.red()

    elif not player.queue and not player.is_playing:
        embed.set_author(name='已結束', icon_url="https://cdn.discordapp.com/emojis/987645074450034718.webp")

        embed.colour = Colour.red()

    loop_mode_text = {
        0: "關閉",
        1: "單曲循環",
        2: "整個佇列循環"
    }

    if player.current:
        embed.title = player.current.title
        embed.description = "`Placeholder / Progress Bar`"

        embed.add_field(name="👤 作者", value=player.current.author, inline=True)
        embed.add_field(name="👥 點播者", value=f"<@{player.current.requester}>", inline=True)
        embed.add_field(name="🔁 重複播放模式", value=loop_mode_text[player.loop], inline=True)

        embed.add_field(
            name="📃 播放序列",
            value=('\n'.join(
                [
                    f"**[{index + 1}]** {track.title}"
                    for index, track in enumerate(player.queue[:5])
                ]) + ("\n還有更多..." if len(player.queue) > 5 else "")) or "空",
            inline=True
        )
        embed.add_field(
            name="⚙️ 已啟用效果器",
            value=', '.join([key.capitalize() for key in player.filters]) or "無",
            inline=True
        )
        embed.add_field(name="🔀 雖機播放", value="開" if player.shuffle else "關", inline=True)

    else:
        embed.title = "未在播放歌曲"

    return embed
