from disnake import Embed


class SuccessEmbed(Embed):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title="✅ | " + title, description=description, color=0x0f9d58, **kwargs)


class InfoEmbed(Embed):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title="ℹ️ | " + title, description=description, color=0x4285f4, **kwargs)


class LoadingEmbed(Embed):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title="⌛ | " + title, description=description, color=0x4285F4, **kwargs)


class WarningEmbed(Embed):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title="⚠ | " + title, description=description, color=0xf4b400, **kwargs)


class ErrorEmbed(Embed):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title="❌ | " + title, description=description, color=0xdb4437, **kwargs)
