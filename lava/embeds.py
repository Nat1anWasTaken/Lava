from typing import Union

from disnake import Embed, Localized


class SuccessEmbed(Embed):
    def __init__(
        self,
        title: Union[str, Localized],
        description: Union[str, Localized] = None,
        **kwargs,
    ):
        if isinstance(title, Localized):
            title = title.string

        if isinstance(description, Localized):
            description = description.string

        super().__init__(
            title="✅ | " + title, description=description, color=0x0F9D58, **kwargs
        )


class InfoEmbed(Embed):
    def __init__(
        self,
        title: Union[str, Localized],
        description: Union[str, Localized] = None,
        **kwargs,
    ):
        if isinstance(title, Localized):
            title = title.string

        if isinstance(description, Localized):
            description = description.string

        super().__init__(
            title="ℹ️ | " + title, description=description, color=0x4285F4, **kwargs
        )


class LoadingEmbed(Embed):
    def __init__(
        self,
        title: Union[str, Localized],
        description: Union[str, Localized] = None,
        **kwargs,
    ):
        if isinstance(title, Localized):
            title = title.string

        if isinstance(description, Localized):
            description = description.string

        super().__init__(
            title="⌛ | " + title, description=description, color=0x4285F4, **kwargs
        )


class WarningEmbed(Embed):
    def __init__(
        self,
        title: Union[str, Localized],
        description: Union[str, Localized] = None,
        **kwargs,
    ):
        if isinstance(title, Localized):
            title = title.string

        if isinstance(description, Localized):
            description = description.string

        super().__init__(
            title="⚠ | " + title, description=description, color=0xF4B400, **kwargs
        )


class ErrorEmbed(Embed):
    def __init__(
        self,
        title: Union[str, Localized],
        description: Union[str, Localized] = None,
        **kwargs,
    ):
        if isinstance(title, Localized):
            title = title.string

        if isinstance(description, Localized):
            description = description.string

        super().__init__(
            title=" | " + title, description=description, color=0xDB4437, **kwargs
        )
