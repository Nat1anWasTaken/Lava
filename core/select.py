from typing import Union

from disnake import SelectOption
from disnake.ui import StringSelect



class Dropdown(StringSelect[SelectOption]):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)