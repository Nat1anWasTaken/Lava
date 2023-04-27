import re
from os import getpid

from disnake import Option, ApplicationCommandInteraction, OptionType, OptionChoice, ButtonStyle, Localized, Embed
from disnake.ext import commands
from disnake.ext.commands import Cog
from disnake.ui import Button
from disnake_ext_paginator import Paginator
from lavalink import DefaultPlayer, LoadResult, LoadType, Timescale, Tremolo, Vibrato, LowPass, Rotation, Equalizer
from psutil import cpu_percent, virtual_memory, Process

from core.bot import Bot
from core.embeds import ErrorEmbed, SuccessEmbed, InfoEmbed, WarningEmbed
from core.errors import UserInDifferentChannel
from core.utils import ensure_voice, update_display, split_list, bytes_to_gb, get_commit_hash, get_upstream_url, \
    get_current_branch

allowed_filters = {
    "timescale": Timescale,
    "tremolo": Tremolo,
    "vibrato": Vibrato,
    "lowpass": LowPass,
    "rotation": Rotation,
    "equalizer": Equalizer
}


class Commands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(
        name=Localized("info", key="command.info.name"),
        description=Localized("顯示機器人資訊", key="command.info.description")
    )
    async def info(self, interaction: ApplicationCommandInteraction):
        locale = str(interaction.locale)

        embed = Embed(
            title=self.bot.get_text('command.info.embed.title', locale, '機器人資訊'),
            color=0x2b2d31
        )

        embed.add_field(
            name=self.bot.get_text('command.info.embed.start_time', locale, '啟動時間'),
            value=f"<t:{round(Process(getpid()).create_time())}:F>",
            inline=True
        )

        branch = get_current_branch()
        upstream_url = get_upstream_url(branch)

        embed.add_field(
            name=self.bot.get_text('command.info.embed.commit_hash', locale, '版本資訊'),
            value=f"{get_commit_hash()} on {branch} from {upstream_url}",
        )

        embed.add_field(name="​", value="​", inline=True)

        embed.add_field(
            name=self.bot.get_text('command.info.embed.cpu', locale, 'CPU'),
            value=f"{cpu_percent()}%",
            inline=True
        )

        embed.add_field(
            name=self.bot.get_text('command.info.embed.ram', locale, 'RAM'),
            value=f"{round(bytes_to_gb(virtual_memory()[3]), 1)} GB / "
                  f"{round(bytes_to_gb(virtual_memory()[0]), 1)} GB "
                  f"({virtual_memory()[2]}%)",
            inline=True
        )

        embed.add_field(name="​", value="​", inline=True)

        embed.add_field(
            name=self.bot.get_text('command.info.embed.guilds', locale, '伺服器數量'),
            value=len(self.bot.guilds),
            inline=True
        )

        embed.add_field(
            name=self.bot.get_text('command.info.embed.players', locale, '播放器數量'),
            value=len(self.bot.lavalink.player_manager.players),
            inline=True
        )

        embed.add_field(name="​", value="​", inline=True)

        await interaction.response.send_message(
            embed=embed
        )

    @commands.slash_command(
        name=Localized("nowplaying", key="command.nowplaying.name"),
        description=Localized("顯示目前正在播放的歌曲", key="command.nowplaying.description")
    )
    async def nowplaying(self, interaction: ApplicationCommandInteraction):
        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        await update_display(self.bot, player, interaction=interaction)

    @commands.slash_command(
        name=Localized("play", key="command.play.name"),
        description=Localized("播放音樂", key="command.play.description"),
        options=[
            Option(
                name="query",
                description=Localized(
                    "歌曲名稱或網址，支援 YouTube, YouTube Music, SoundCloud, Spotify",
                    key="command.play.option.query"
                ),
                type=OptionType.string,
                autocomplete=True,
                required=True
            ),
            Option(
                name="index",
                description=Localized("要將歌曲放置於當前播放序列的位置", key="command.play.option.index"),
                type=OptionType.integer,
                required=False
            )
        ]
    )
    async def play(self, interaction: ApplicationCommandInteraction, query: str, index: int = None):
        await interaction.response.defer()

        locale = str(interaction.locale)

        await ensure_voice(interaction, should_connect=True)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        player.store("channel", interaction.channel.id)

        # TODO: Add support for spotify, apple music etc...
        url_rx = re.compile(r"https?://(?:www\.)?.+")

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results: LoadResult = await player.node.get_tracks(query)

        # Check locals
        if not results or not results.tracks:
            for source in self.sources:
                result = await source.load_item(self, query)

                if result:
                    results = result

                    break

        if not results or not results.tracks:  # If nothing was found
            return await interaction.edit_original_response(
                embed=ErrorEmbed(
                    self.bot.get_text("command.play.error.no_results.title", locale, "沒有找到任何歌曲"),
                    self.bot.get_text(
                        "command.play.error.no_results.description", locale,
                        "如果你想要使用關鍵字搜尋，請在輸入關鍵字後等待幾秒，搜尋結果將會自動顯示在上方",
                    )
                )
            )

        # Find the index song should be (In front of any autoplay songs)
        if not index:
            index = sum(1 for t in player.queue if t.requester)

        filter_warnings = [
            InfoEmbed(
                title=self.bot.get_text("command.play.filter_warning.title", locale, "提醒"),
                description=str(
                    self.bot.get_text(
                        'command.play.filter_warning.description', locale,
                        '偵測到 效果器正在運作中，\n'
                        '這可能會造成音樂聲音有變形(加速、升高等)的情形產生，\n'
                        '如果這不是你期望的，可以透過效果器的指令來關閉它們\n'
                        '指令名稱通常等於效果器名稱，例如 `/timescale` 就是控制 Timescale 效果器\n\n'
                        '以下是正在運行的效果器：'
                    )
                ) + ' ' + ', '.join([key.capitalize() for key in player.filters])
            )
        ] if player.filters else []

        match results.load_type:
            case LoadType.TRACK:
                player.add(
                    requester=interaction.author.id,
                    track=results.tracks[0], index=index
                )

                # noinspection PyTypeChecker
                await interaction.edit_original_response(
                    embeds=[
                               SuccessEmbed(
                                   self.bot.get_text("command.play.loaded.title", locale, "已加入播放序列"),
                                   {results.tracks[0].title}
                               )
                           ] + filter_warnings
                )

            case LoadType.PLAYLIST:
                # TODO: Ask user if they want to add the whole playlist or just some tracks

                for iter_index, track in enumerate(results.tracks):
                    player.add(
                        requester=interaction.author.id, track=track,
                        index=index + iter_index
                    )

                # noinspection PyTypeChecker
                await interaction.edit_original_response(
                    embeds=[
                               SuccessEmbed(
                                   title=f"{self.bot.get_text('command.play.loaded.title', locale, '已加入播放序列')} {len(results.tracks)} / {results.playlist_info.name}",
                                   description='\n'.join(
                                       [
                                           f"**[{index + 1}]** {track.title}"
                                           for index, track in enumerate(results.tracks[:10])
                                       ]
                                   ) + "..." if len(results.tracks) > 10 else ""
                               )
                           ] + filter_warnings
                )

        # If the player isn't already playing, start it.
        if not player.is_playing:
            await player.play()

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale,
        )

    @commands.slash_command(
        name=Localized("skip", key="command.skip.name"),
        description=Localized("跳過當前播放的歌曲", key="command.skip.description"),
        options=[
            Option(
                name="target",
                description=Localized("要跳到的歌曲編號", key="command.skip.option.target"),
                type=OptionType.integer,
                required=False
            ),
            Option(
                name="move",
                description=Localized(
                    "是否移除目標以前的所有歌曲，如果沒有提供 target，這個參數會被忽略", key="command.skip.option.move"
                ),
                type=OptionType.boolean,
                required=False
            )
        ]
    )
    async def skip(self, interaction: ApplicationCommandInteraction, target: int = None, move: bool = False):
        await interaction.response.defer()

        locale = str(interaction.locale)

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        if not player.is_playing:
            return await interaction.edit_original_response(
                embed=ErrorEmbed(self.bot.get_text("error.nothing_playing", locale, "沒有正在播放的歌曲"))
            )

        if target:
            if len(player.queue) < target or target < 1:
                return await interaction.edit_original_response(
                    embed=ErrorEmbed(self.bot.get_text("error.invalid_track_number", locale, "無效的歌曲編號"))
                )

            if move:
                player.queue.insert(0, player.queue.pop(target - 1))

            else:
                player.queue = player.queue[target - 1:]

        await player.skip()

        await interaction.edit_original_response(
            embed=SuccessEmbed(self.bot.get_text("command.skip.success", locale, "已跳過歌曲"))
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )

    @commands.slash_command(
        name=Localized("remove", key="command.remove.name"),
        description=Localized("移除歌曲", key="command.remove.description"),
        options=[
            Option(
                name="target",
                description=Localized("要移除的歌曲編號", key="command.remove.option.target"),
                type=OptionType.integer,
                required=True
            )
        ]
    )
    async def remove(self, interaction: ApplicationCommandInteraction, target: int):
        await interaction.response.defer()

        locale = str(interaction.locale)

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        if len(player.queue) < target or target < 1:
            return await interaction.edit_original_response(
                embed=ErrorEmbed(self.bot.get_text("error.invalid_track_number", locale, "無效的歌曲編號"))
            )

        player.queue.pop(target - 1)

        await interaction.edit_original_response(
            embed=SuccessEmbed(self.bot.get_text("command.remove.success", locale, "已移除歌曲"))
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )

    @commands.slash_command(
        name=Localized("clean", key="command.clean.name"),
        description=Localized(
            "清除播放序列", key="command.clean.description"
        )
    )
    async def clean(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        locale = str(interaction.locale)

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        player.queue.clear()

        await interaction.edit_original_response(
            embed=SuccessEmbed(self.bot.get_text("command.clean.success", locale, "已清除播放序列"))
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )

    @commands.slash_command(
        name=Localized("pause", key="command.pause.name"),
        description=Localized("暫停當前播放的歌曲", key="command.pause.description")
    )
    async def pause(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        locale = str(interaction.locale)

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        if not player.is_playing:
            return await interaction.edit_original_response(
                embed=ErrorEmbed(self.bot.get_text("error.nothing_playing", locale, "沒有正在播放的歌曲"))
            )

        await player.set_pause(True)

        await interaction.edit_original_response(
            embed=SuccessEmbed(self.bot.get_text("command.pause.success", locale, "已暫停歌曲"))
        )

    @commands.slash_command(
        name=Localized("resume", key="command.resume.name"),
        description=Localized("恢復當前播放的歌曲", key="command.resume.description")
    )
    async def resume(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        locale = str(interaction.locale)

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        if not player.paused:
            return await interaction.edit_original_response(
                embed=ErrorEmbed(self.bot.get_text("command.pause.error.nothing_paused", locale, "沒有暫停的歌曲"))
            )

        await player.set_pause(False)

        await interaction.edit_original_response(
            embed=SuccessEmbed(self.bot.get_text("command.resume.success", locale, "已繼續歌曲"))
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )

    @commands.slash_command(
        name=Localized("stop", key="command.stop.name"),
        description=Localized("停止播放並清空播放序列", key="command.stop.description")
    )
    async def stop(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        await player.stop()
        player.queue.clear()

        await update_display(self.bot, player, await interaction.original_response())

    @commands.slash_command(
        name=Localized("connect", key="command.connect.name"),
        description=Localized("連接至你當前的語音頻道", key="command.connect.description")
    )
    async def connect(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        locale = str(interaction.locale)

        try:
            await ensure_voice(interaction, should_connect=True)

            await interaction.edit_original_response(
                embed=SuccessEmbed(self.bot.get_text("command.connect.success", locale, "已連接至語音頻道"))
            )

        except UserInDifferentChannel:
            player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

            await interaction.edit_original_response(
                embed=WarningEmbed(
                    self.bot.get_text("command.connect.error.already_in_channel.title", locale, "警告"),
                    self.bot.get_text(
                        "command.connect.error.already_in_channel.description", locale,
                        "機器人已經在一個頻道中了，繼續移動將會中斷對方的音樂播放，是否要繼續?"
                    )
                ),
                components=[
                    Button(
                        label=str(
                            self.bot.get_text("command.connect.error.already_in_channel.continue", locale, "繼續")
                        ),
                        style=ButtonStyle.green, custom_id="continue"
                    )
                ]
            )

            try:
                await self.bot.wait_for(
                    "button_click",
                    check=lambda i: i.data.custom_id in ["continue"] and i.user.id == interaction.user.id,
                    timeout=10
                )

            except TimeoutError:
                await interaction.edit_original_response(
                    embed=ErrorEmbed(
                        self.bot.get_text("command.connect.error.already_in_channel.cancel", locale, "已取消")
                    ),
                    components=[]
                )

                return

            await player.stop()
            player.queue.clear()

            await interaction.guild.voice_client.disconnect(force=False)

            await ensure_voice(interaction, should_connect=True)

            await interaction.edit_original_response(
                embed=SuccessEmbed(self.bot.get_text("command.connect.success", locale, "已連接至語音頻道")),
                components=[]
            )

        finally:
            await update_display(
                bot=self.bot,
                player=player or interaction.bot.lavalink.player_manager.get(interaction.guild.id),
                new_message=await interaction.original_response(),
                delay=5,
                locale=interaction.locale
            )

    @commands.slash_command(
        name=Localized("disconnect", key="command.disconnect.name"),
        description=Localized(
            "斷開與語音頻道的連接", key="command.disconnect.description"
        )
    )
    async def disconnect(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        await player.stop()
        player.queue.clear()

        await interaction.guild.voice_client.disconnect(force=False)

        await update_display(self.bot, player, await interaction.original_response(), locale=interaction.locale)

    @commands.slash_command(
        name=Localized("queue", key="command.queue.name"),
        description=Localized("顯示播放序列", key="command.queue.description")
    )
    async def queue(self, interaction: ApplicationCommandInteraction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        locale = str(interaction.locale)

        if not player or not player.queue:
            return await interaction.response.send_message(
                embed=ErrorEmbed(self.bot.get_text("command.queue.error.empty", locale, "播放序列為空"))
            )

        pages: list[InfoEmbed] = []

        for iteration, songs_in_page in enumerate(split_list(player.queue, 10)):
            pages.append(
                InfoEmbed(
                    title=self.bot.get_text("command.queue.title", locale, "播放序列"),
                    description='\n'.join(
                        [
                            f"**[{index + 1 + (iteration * 10)}]** {track.title}"
                            f" {self.bot.get_icon('control.autoplay', '🔥') if not track.requester else ''}"
                            for index, track in enumerate(songs_in_page)
                        ]
                    )
                )
            )

        paginator = Paginator(
            timeout=60,
            previous_button=Button(
                style=ButtonStyle.blurple, emoji=self.bot.get_icon('control.previous', '⏪')
            ),
            next_button=Button(
                style=ButtonStyle.blurple,
                emoji=self.bot.get_icon('control.next', '⏩')
            ),
            trash_button=Button(
                style=ButtonStyle.red,
                emoji=self.bot.get_icon('control.stop', '⏹️')
            ),
            page_counter_style=ButtonStyle.green,
            interaction_check_message=ErrorEmbed(
                self.bot.get_text("command.queue.error.interaction_check_message", locale, "沒事戳這顆幹嘛？")
            )
        )

        await paginator.start(interaction, pages)

    @commands.slash_command(
        name=Localized("repeat", key="command.repeat.name"),
        description=Localized("更改重複播放模式", key="command.repeat.description"),
        options=[
            Option(
                name="mode",
                description=Localized("重複播放模式", key="command.repeat.option.mode"),
                type=OptionType.string,
                choices=[
                    OptionChoice(
                        name=Localized('關閉', key='repeat_mode.off'),
                        value=f"{Localized('關閉', key='repeat_mode.off')}/0"
                    ),
                    OptionChoice(
                        name=Localized('單曲', key='repeat_mode.song'),
                        value=f"{Localized('單曲', key='repeat_mode.song')} 單曲/1"
                    ),
                    OptionChoice(
                        name=Localized('整個序列', key='repeat_mode.queue'),
                        value=f"{Localized('整個序列', key='repeat_mode.queue')} 整個序列/2"
                    )
                ],
                required=True
            )
        ]
    )
    async def repeat(self, interaction: ApplicationCommandInteraction, mode: str):
        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        locale = str(interaction.locale)

        player.set_loop(int(mode.split("/")[1]))

        await interaction.response.send_message(
            embed=SuccessEmbed(
                f"{self.bot.get_text('command.repeat.success', locale, '成功將重複播放模式更改為')}: {mode.split('/')[0]}"
            )
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )

    @commands.slash_command(
        name=Localized("shuffle", key="command.shuffle.name"),
        description=Localized("切換隨機播放模式", key="command.shuffle.description")
    )
    async def shuffle(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        locale = str(interaction.locale)

        player.set_shuffle(not player.shuffle)

        await interaction.edit_original_response(
            embed=SuccessEmbed(
                f"{self.bot.get_text('command.shuffle.success', locale, '隨機播放模式')}：{self.bot.get_text('enable', locale, '開啟') if player.shuffle else self.bot.get_text('disable', locale, '關閉')}"
            )
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )

    @play.autocomplete("query")
    async def search(self, interaction: ApplicationCommandInteraction, query: str):
        if re.match(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", query):
            return []

        if not query:
            return []

        choices = []

        result = await self.bot.lavalink.get_tracks(f"ytsearch:{query}")

        for track in result.tracks:
            choices.append(
                OptionChoice(
                    name=f"{track.title[:80]} by {track.author[:16]}", value=track.uri
                )
            )

        return choices

    @commands.slash_command(
        name=Localized("timescale", key="command.timescale.name"),
        description=Localized("修改歌曲的速度、音調", key="command.timescale.description"),
        options=[
            Option(
                name="speed",
                description=Localized("速度 (≥ 0.1)", key="command.timescale.option.speed"),
                type=OptionType.number,
                required=False
            ),
            Option(
                name="pitch",
                description=Localized("音調 (≥ 0.1)", key="command.timescale.option.pitch"),
                type=OptionType.number,
                required=False
            ),
            Option(
                name="rate",
                description=Localized("速率 (≥ 0.1)", key="command.timescale.option.rate"),
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def timescale(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "timescale", **kwargs)

    @commands.slash_command(
        name=Localized("tremolo", key="command.tremolo.name"),
        description=Localized("為歌曲增加一個「顫抖」的效果", key="command.tremolo.description"),
        options=[
            Option(
                name="frequency",
                description=Localized("頻率 (0 < n)", key="command.tremolo.option.frequency"),
                type=OptionType.number,
                required=False
            ),
            Option(
                name="depth",
                description=Localized("強度 (0 < n ≤ 1)", key="command.tremolo.option.depth"),
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def tremolo(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "tremolo", **kwargs)

    @commands.slash_command(
        name=Localized("vibrato", key="command.vibrato.name"),
        description=Localized("為歌曲增加一個「震動」的效果", key="command.vibrato.description"),
        options=[
            Option(
                name="frequency",
                description=Localized("頻率 (0 < n ≤ 14)", key="command.vibrato.option.frequency"),
                type=OptionType.number,
                required=False
            ),
            Option(
                name="depth",
                description=Localized("強度 (0 < n ≤ 1)", key="command.vibrato.option.depth"),
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def vibrato(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "vibrato", **kwargs)

    @commands.slash_command(
        name=Localized("rotation", key="command.rotation.name"),
        description=Localized("8D 環繞效果", key="command.rotation.description"),
        options=[
            Option(
                name="rotation_hz",
                description=Localized("頻率 (0 ≤ n)", key="command.rotation.option.rotation_hz"),
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def rotation(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "rotation", **kwargs)

    @commands.slash_command(
        name=Localized("lowpass", key="command.lowpass.name"),
        description=Localized("低音增強 (削弱高音)", key="command.lowpass.description"),
        options=[
            Option(
                name="smoothing",
                description=Localized("強度 (1 < n)", key="command.lowpass.option.smoothing"),
                type=OptionType.number,
                required=False
            )
        ]
    )
    async def lowpass(self, interaction: ApplicationCommandInteraction, **kwargs):
        await self.update_filter(interaction, "lowpass", **kwargs)

    @commands.slash_command(
        name=Localized("bassboost", key="command.bassboost.name"),
        description=Localized("低音增強 (等化器)", key="command.bassboost.description"),
    )
    async def bassboost(self, interaction: ApplicationCommandInteraction):
        player: DefaultPlayer = self.bot.lavalink.player_manager.get(
            interaction.guild.id
        )

        audio_filter = player.get_filter("equalizer")

        if not audio_filter:
            await self.update_filter(
                interaction, "equalizer", player=player,
                bands=[(0, 0.3), (1, 0.2), (2, 0.1)]
            )
            return

        await self.update_filter(interaction, "equalizer", player=player)

    async def update_filter(self, interaction: ApplicationCommandInteraction, filter_name: str,
                            player: DefaultPlayer = None, **kwargs):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=False)

        locale = str(interaction.locale)

        if not player:
            player: DefaultPlayer = self.bot.lavalink.player_manager.get(
                interaction.guild.id
            )

        if not kwargs:
            await player.remove_filter(filter_name)

            await interaction.edit_original_response(
                embed=SuccessEmbed(
                    f"{self.bot.get_text('command.filters.removed', locale, '已移除效果器')}：{allowed_filters[filter_name].__name__}"
                )
            )

            await update_display(self.bot, player, await interaction.original_response(), delay=5)

            return

        audio_filter = player.get_filter(
            filter_name
        ) or allowed_filters[filter_name]()

        try:
            audio_filter.update(**kwargs)

        except ValueError:
            await interaction.edit_original_response(
                embed=ErrorEmbed(self.bot.get_text('command.filters.invalid_params', locale, '請輸入有效的參數'))
            )
            return

        await player.set_filter(audio_filter)

        await interaction.edit_original_response(
            embed=SuccessEmbed(
                f"{self.bot.get_text('command.filters.set', locale, '已設置效果器')}：{allowed_filters[filter_name].__name__}"
            )
        )

        await update_display(
            self.bot, player, await interaction.original_response(), delay=5, locale=interaction.locale
        )


def setup(bot):
    bot.add_cog(Commands(bot))
