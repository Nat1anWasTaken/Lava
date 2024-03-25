import json
import uuid

from disnake.ui import Modal, TextInput
from disnake import TextInputStyle, ModalInteraction
from lavalink import LoadResult
from typing import Optional

from lava.bot import Bot
from lava.embeds import LoadingEmbed, SuccessEmbed, ErrorEmbed


class PlaylistModal(Modal):
    def __init__(self, name: str, bot: Bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.name = name

        self.tracks = []

        self.append_component(
            TextInput(
                label="歌曲連結 (格式為第一首後按下Enter再貼連結，最多25個)",
                placeholder="請將連結貼至輸入框中",
                custom_id="link",
                style=TextInputStyle.paragraph,
            )
        )

    async def callback(self, interaction: ModalInteraction) -> Optional[LoadResult]:
        with open(f"./playlist/{interaction.user.id}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        value = interaction.text_values.get("link", None)
        if (
            not len(value.split("\n")) > 25
            and not (len(data[self.name]["data"]["tracks"]) + len(value.split("\n")))
            > 25
        ):
            await interaction.response.send_message(
                embed=LoadingEmbed(title="正在讀取中....")
            )

            for query in value.split("\n"):
                result = await self.bot.lavalink.get_tracks(query, check_local=True)
                for track in result.tracks:
                    data[self.name]["data"]["tracks"].append(
                        {
                            "encoded": track.track,
                            "info": {
                                "identifier": track.identifier,
                                "isSeekable": track.is_seekable,
                                "author": track.author,
                                "length": track.duration,
                                "isStream": track.stream,
                                "position": track.position,
                                "title": track.title,
                                "uri": track.uri,
                                "sourceName": track.source_name,
                                "artworkUrl": track.artwork_url,
                                "isrc": track.isrc,
                            },
                            "pluginInfo": track.plugin_info,
                            "userData": track.user_data,
                        },
                    )

            for name in data.keys():
                if uuid.uuid5(uuid.NAMESPACE_DNS, name) == uuid.UUID(self.name):
                    self.name = name
                    break

            data[self.name]["data"]["tracks"] = data[self.name]["data"]["tracks"]

            with open(
                f"./playlist/{interaction.user.id}.json", "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            await interaction.edit_original_response(
                embed=SuccessEmbed(title="添加成功!")
            )
        else:
            await interaction.edit_original_response(
                embed=ErrorEmbed(
                    title="你給的連結太多了或是歌單超出限制了! (最多25個)",
                    description=f"目前歌單中的歌曲數量: {len(data[self.name]['data']['tracks'])}",
                )
            )
