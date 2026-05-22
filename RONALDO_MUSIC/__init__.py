from RONALDO_MUSIC.core.bot import RONALDO
from RONALDO_MUSIC.core.dir import dirr
from RONALDO_MUSIC.core.git import git
from RONALDO_MUSIC.core.userbot import Userbot
from RONALDO_MUSIC.misc import dbb, heroku

from SafoneAPI import SafoneAPI
from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = RONALDO()
api = SafoneAPI()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
