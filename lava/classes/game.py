from disnake import TextChannel, Embed, ApplicationCommandInteraction

from typing import Optional

from datetime import datetime

import asyncio


class Game:
    def __init__(
        self,
        guild_id: int,
        title: str,
        genre: str,
        channel: TextChannel,
        rounds: int,
        round_delay: int,
        round_length: int,
        victory_score: int,
        match_percentage: float,
    ):
        self.genre = genre
        self.title = title
        self.rounds = rounds
        self.round_delay = round_delay
        self.round_length = round_length
        self.victory_score = victory_score
        self.match_percentage = match_percentage
        self.channel = channel

        self._ready = False
        self._round = 0
        self._guild_id = guild_id

    async def start(self, interaction: ApplicationCommandInteraction):
        embed = self.__generate_game_embed()

        await interaction.response.send_message(embed=embed)

        await asyncio.sleep(self.round_delay)

        await interaction.edit_original_response(embed)

    def __generate_game_embed(self):
        embed = Embed()

        embed.title = self.title

        embed.description = (
            f"第{self._round}回合將於 <t:{datetime.timestamp(datetime.now()) + self.round_delay}:R> 開始"
            if self._ready is False
            else f"# 第{self._round}回合：\n - 請聆聽以下歌曲並答出歌名和演唱者。 \n - 準確率需達 {self.match_percentage * 100} %。"
        )

        return embed
