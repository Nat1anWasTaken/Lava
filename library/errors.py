from disnake.abc import Connectable


class UserNotInVoice(Exception):
    pass


class BotNotInVoice(Exception):
    pass


class MissingVoicePermissions(Exception):
    pass


class UserInDifferentChannel(Exception):
    def __init__(self, voice: Connectable, *args):
        self.voice = voice

        super().__init__(*args)


class LoadError(Exception):
    pass
