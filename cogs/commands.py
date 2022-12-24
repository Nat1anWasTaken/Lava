import re

from disnake import Option, ApplicationCommandInteraction, OptionType, OptionChoice
from disnake.ext import commands
from disnake.ext.commands import Cog
from lavalink import DefaultPlayer, LoadResult, LoadType, Timescale, Tremolo, Vibrato, LowPass, Rotation

from core.classes import Bot
from core.embeds import ErrorEmbed, SuccessEmbed
from library.functions import ensure_voice, update_display

allowed_filters = {
    "timescale": Timescale,
    "tremolo": Tremolo,
    "vibrato": Vibrato,
    "lowpass": LowPass,
    "rotation": Rotation
}


class Commands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(
        name="nowplaying",
        description="顯示目前正在播放的歌曲"
    )
    async def nowplaying(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        await update_display(self.bot, player, await interaction.original_response())

    @commands.slash_command(
        name="play",
        description="播放一首歌曲",
        options=[
            Option(
                name="query",
                description="歌曲名稱或網址，支援 YouTube, YouTube Music, SoundCloud, Spotify",
                type=OptionType.string,
                autocomplete=True,
                required=True
            ),
            Option(
                name="index",
                description="要將歌曲放置於當前播放序列的位置",
                type=OptionType.integer,
                required=False
            )
        ]
    )
    async def play(self, interaction: ApplicationCommandInteraction, query: str, index: int = None):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=True)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        player.store("channel", interaction.channel.id)

        # TODO: Add support for spotify, apple music etc...
        url_rx = re.compile(r"https?://(?:www\.)?.+")

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results: LoadResult = await player.node.get_tracks(query, check_local=True)

        if not results or not results.tracks:
            return await interaction.edit_original_response(embed=ErrorEmbed("沒有找到任何歌曲"))

        match results.load_type:
            case LoadType.TRACK:
                player.add(requester=interaction.author.id, track=results.tracks[0], index=index - 1 if index else None)

                await interaction.edit_original_response(
                    embed=SuccessEmbed(f"已加入播放序列", f"{results.tracks[0].title}")
                )

            case LoadType.PLAYLIST:
                # TODO: Ask user if they want to add the whole playlist or just some tracks

                for iter_index, track in enumerate(results.tracks):
                    player.add(
                        requester=interaction.author.id, track=track,
                        index=index or len(player.queue) - 1 + iter_index
                    )

                await interaction.edit_original_response(
                    embed=SuccessEmbed(
                        f"已將 {results.playlist_info.name} 中的 {len(results.tracks)} 首歌曲加入播放序列",
                        '\n'.join(
                            [
                                f"**[{index + 1}]** {track.title}"
                                for index, track in enumerate(results.tracks[:10])
                            ]
                        ) + "..." if len(results.tracks) > 10 else ""
                    )
                )

        # If the player isn't already playing, start it.
        if not player.is_playing:
            await player.play()

        await update_display(self.bot, player, await interaction.original_response(), delay=5)

    @commands.slash_command(
        name="skip",
        description="跳過當前播放的歌曲",
        options=[
            Option(
                name="target",
                description="要跳到的歌曲編號",
                type=OptionType.integer,
                required=False
            ),
            Option(
                name="move",
                description="是否移除目標以前的所有歌曲，如果沒有提供 target，這個參數會被忽略",
                type=OptionType.boolean,
                required=False
            )
        ]
    )
    async def skip(self, interaction: ApplicationCommandInteraction, target: int = None, move: bool = False):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not player.is_playing:
            return await interaction.edit_original_response(embed=ErrorEmbed("沒有正在播放的歌曲"))

        if target:
            if len(player.queue) < target or target < 1:
                return await interaction.edit_original_response(embed=ErrorEmbed("無效的歌曲編號"))

            if move:
                player.queue.insert(0, player.queue.pop(target - 1))

            else:
                player.queue = player.queue[target - 1:]

        await player.skip()

        await interaction.edit_original_response(embed=SuccessEmbed("已跳過歌曲"))

        await update_display(self.bot, player, await interaction.original_response(), delay=5)

    @commands.slash_command(
        name="pause",
        description="暫停當前播放的歌曲"
    )
    async def pause(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not player.is_playing:
            return await interaction.edit_original_response(embed=ErrorEmbed("沒有正在播放的歌曲"))

        await player.set_pause(True)

        await interaction.edit_original_response(embed=SuccessEmbed("已暫停歌曲"))

    @commands.slash_command(
        name="resume",
        description="恢復當前播放的歌曲"
    )
    async def resume(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not player.paused:
            return await interaction.edit_original_response(embed=ErrorEmbed("沒有暫停的歌曲"))

        await player.set_pause(False)

        await interaction.edit_original_response(embed=SuccessEmbed("已恢復歌曲"))

        await update_display(self.bot, player, await interaction.original_response(), delay=5)

    @commands.slash_command(
        name="stop",
        description="停止播放並清空播放序列"
    )
    async def stop(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        await player.stop()

        await update_display(self.bot, player, await interaction.original_response())

    @commands.slash_command(
        name="repeat",
        description="更改重複播放模式",
        options=[
            Option(
                name="mode",
                description="重複播放模式",
                type=OptionType.string,
                choices=[
                    OptionChoice(name="關閉", value="關閉/0"),
                    OptionChoice(name="單曲", value="單曲/1"),
                    OptionChoice(name="播放序列", value="播放序列/2")
                ],
                required=True
            )
        ]
    )
    async def repeat(self, interaction: ApplicationCommandInteraction, mode: str):
        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        player.set_loop(int(mode.split("/")[1]))

        await interaction.response.send_message(embed=SuccessEmbed(f"成功將重複播放模式更改為: {mode.split('/')[0]}"))

    @commands.slash_command(name="shuffle", description="切換隨機播放模式")
    async def shuffle(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        player.set_shuffle(not player.shuffle)

        await interaction.edit_original_response(
            embed=SuccessEmbed(f"已{'開啟' if player.shuffle else '關閉'}隨機播放模式")
        )

        await update_display(self.bot, player, await interaction.original_response(), delay=5)

    @play.autocomplete("query")
    async def search(self, interaction: ApplicationCommandInteraction, query: str):
        if query and "https://open.spotify.com/" not in query:
            choices = []

            result = await self.bot.lavalink.get_tracks(f"ytsearch:{query}")

            for track in result.tracks:
                choices.append(OptionChoice(name=f"{track.title[:80]} by {track.author[:16]}", value=track.uri))

            return choices

        return []

    @commands.slash_command(
        name="timescale", description="修改歌曲的速度、音調",
        options=[
            Option(
                name="speed",
                description="速度 (≥ 0.1)",
                type=OptionType.number,
                required=False
            ),
            Option(
                name="pitch",
                description="音調 (≥ 0.1)",
                type=OptionType.number,
                required=False
            ),
            Option(
                name="rate",
                description="速率 (≥ 0.1)",
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def timescale(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "timescale", **kwargs)

    @commands.slash_command(
        name="tremolo", description="為歌曲增加一個「顫抖」的效果",
        options=[
            Option(
                name="frequency",
                description="頻率 (0 < n)",
                type=OptionType.number,
                required=False
            ),
            Option(
                name="depth",
                description="強度 (0 < n ≤ 1)",
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def tremolo(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "tremolo", **kwargs)

    @commands.slash_command(
        name="vibrato", description="為歌曲增加一個「震動」的效果",
        options=[
            Option(
                name="frequency",
                description="頻率 (0 < n ≤ 14)",
                type=OptionType.number,
                required=False
            ),
            Option(
                name="depth",
                description="強度 (0 < n ≤ 1)",
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def vibrato(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "vibrato", **kwargs)

    @commands.slash_command(
        name="rotation", description="8D 環繞效果",
        options=[
            Option(
                name="rotation_hz",
                description="頻率 (0 ≤ n)",
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def rotation(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "rotation", **kwargs)

    @commands.slash_command(
        name="lowpass", description="低音增強 (削弱高音)",
        options=[
            Option(
                name="smoothing",
                description="強度 (1 < n)",
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def lowpass(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "lowpass", **kwargs)

    async def update_filter(self, interaction: ApplicationCommandInteraction, filter_name: str, **kwargs):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not kwargs:
            await player.remove_filter(filter_name)

            await interaction.edit_original_response(
                embed=SuccessEmbed(f"已移除 {allowed_filters[filter_name].__name__} 效果器，可能需要幾秒鐘才能發揮效果")
            )

            await update_display(self.bot, player, await interaction.original_response(), delay=5)

            return

        audio_filter = player.get_filter(filter_name) or allowed_filters[filter_name]()

        try:
            audio_filter.update(**kwargs)
        except ValueError:
            await interaction.edit_original_response(embed=ErrorEmbed("請輸入有效的參數"))
            return

        await player.set_filter(audio_filter)

        await interaction.edit_original_response(
            embed=SuccessEmbed(f"已設置 {allowed_filters[filter_name].__name__} 效果器，可能需要幾秒鐘才能發揮效果")
        )

        await update_display(self.bot, player, await interaction.original_response(), delay=5)


def setup(bot):
    bot.add_cog(Commands(bot))
