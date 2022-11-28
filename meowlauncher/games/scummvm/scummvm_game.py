import logging
from collections.abc import Mapping
from pathlib import Path

from meowlauncher import input_info
from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.configured_runner import ConfiguredRunner
from meowlauncher.game import Game
from meowlauncher.games.common.pc_common_info import \
    look_for_icon_in_folder
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.launcher import Launcher
from meowlauncher.util.region_info import Language, get_language_by_short_code

from .scummvm_config import scummvm_config

logger = logging.getLogger(__name__)

def format_platform(platform: str) -> str:
	"""Converts short platform code into something more human readable (uses same names as emulated_platforms)
	See also https://github.com/scummvm/scummvm/blob/master/common/platform.cpp#L28"""
	return {
		'2gs': 'Apple IIgs',
		'apple2': 'Apple II',
		'3do': '3DO',
		'acorn': 'Acorn Archimedes',
		'amiga': 'Amiga',
		'atari8': 'Atari 8-bit',
		'atari': 'Atari ST',
		'c64': 'C64',
		'pc': 'DOS',
		'pc98': 'PC-98',
		'wii': 'Wii',
		'coco': 'Tandy CoCo',
		'coco3': 'Tandy CoCo',
		'fmtowns': 'FM Towns',
		'linux': 'Linux',
		'macintosh': 'Mac',
		'pce': 'PC Engine CD', #All the PC Engine games supported would be CDs, not cards
		'nes': 'NES',
		'segacd': 'Mega CD',
		'windows': 'Windows',
		'playstation': 'PlayStation',
		'playstation2': 'PS2',
		'xbox': 'Xbox',
		'cdi': 'CD-i',
		'ios': 'iOS',
		'android': 'Android',
		'os2': 'OS/2',
		'beos': 'BeOS',
		'ppc': 'PocketPC',
		'megadrive': 'Mega Drive',
		'saturn': 'Saturn',
		'pippin': 'Pippin',
		'macintosh2': 'Mac',
		'shockwave': 'Shockwave',
		'zx': 'ZX Spectrum',
		'ti994': 'TI-99',
	}.get(platform, platform.title())

class ScummVMGame(Game):
	def __init__(self, game_id: str):
		super().__init__()
		#The [game_id] is also user-modifiable and shouldn't be relied on to mean anything, but it is used for scummvm to actually launch the game and can be trusted to be unique
		self.game_id = game_id
		self.options = {}
		for k, v in scummvm_config.scummvm_ini.items(game_id):
			self.options[k] = v

		self.add_metadata()

	@property
	def name(self) -> str:
		name = self.options.get('description', self.game_id)
		name = name.replace('/', ') (') #Names are usually something like Cool Game (CD/DOS/English); we convert it to Cool Game (CD) (DOS) (English) to make it work better with disambiguate etc		
		return name

	def __str__(self) -> str:
		return f'{self.name} ({self.game_id})'

	@staticmethod
	def _engine_list_to_use() -> Mapping[str, str]:
		return scummvm_config.scummvm_engines

	@property
	def engine(self) -> str | None:
		"""Display name for the engine"""
		engine_id = self.options.get('engineid')
		if engine_id:
			return self._engine_list_to_use().get(engine_id, engine_id)
		return None

	@property
	def path(self) -> Path | None:
		"""Path to folder containing game files (or filename in case of Glk etc)"""
		pathstr = self.options.get('path')
		if not pathstr:
			return None
		path = Path(pathstr) #path
		filename = self.options.get('filename') #Glk has this, as it is just one file; stops us looking for icons in a folder where we shouldn't etc
		return path / filename if filename else path

	@property
	def language(self) -> Language | None:
		"""Language specified by the "language" option"""
		language_code = self.options.get('language')
		if not language_code:
			return None
		if language_code == 'br':
			return get_language_by_short_code('Pt-Br')
		if language_code == 'cn':
			return get_language_by_short_code('Zh-Hans')
		if language_code == 'tw':
			return get_language_by_short_code('Zh-Hant')
		if language_code == 'gb':
			return get_language_by_short_code('En-GB')
		if language_code == 'us':
			return get_language_by_short_code('En-US')
		if language_code == 'be':
			return get_language_by_short_code('Nl-BE')
		if language_code == 'nb': #Bokmål
			return get_language_by_short_code('No')
		if language_code == 'se':
			#…That's the region code for Sweden, not the language code for Swedish, so that's odd but that's how it ends up being
			return get_language_by_short_code('Sv')
		#There is an array called "g_obsoleteLanguages" here
		if language_code == 'cz':
			return get_language_by_short_code('Cs')
		if language_code == 'gr':
			return get_language_by_short_code('El')
		if language_code == 'hb':
			return get_language_by_short_code('He')
		if language_code == 'jp':
			return get_language_by_short_code('Ja')
		if language_code == 'kr':
			return get_language_by_short_code('Ko')
		if language_code == 'nz':
			return get_language_by_short_code('Zh')
		if language_code == 'zh-cn':
			return get_language_by_short_code('Zh-Hans')

		lang = get_language_by_short_code(language_code, case_insensitive=True)
		if not lang:
			logger.info('Unknonw language in ScummVM game, returning None: %s', language_code)
		return lang

	@property
	def original_platform(self) -> str | None:
		"""Platform that this version of the game was released for (uses same wording as emulated_platforms)"""
		platform = self.options.get('platform')
		if not platform:
			return None
		if platform == 'amiga' and self.options.get('extra') == 'CD32':
			return 'Amiga CD32'
		return format_platform(platform)
		
	def add_metadata(self) -> None:
		self.info.input_info.add_option([input_info.Mouse(), input_info.Keyboard()]) #Can use gamepad if you enable it, but I guess to add that as input_info I'd have to know exactly how many buttons and sticks etc it uses
		self.info.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		self.info.categories = ('Games', ) #Safe to assume this by default
		if self.options.get('gameid') == 'agi-fanmade':
			self.info.categories = ('Homebrew', )
		#genre/subgenre is _probably_ always point and click adventure, but maybe not? (Plumbers is arguably a visual novel (don't @ me), and there's something about some casino card games in the list of supported games)
		#Would be nice to set things like developer/publisher/year but can't really do that unfortunately
		#Let series and series_index be detected by series_detect
		
		engine = self.engine
		if engine:
			self.info.specific_info['Engine'] = engine
		extra = self.options.get('extra')
		if extra:
			self.info.specific_info['Version'] = extra #Hmm, I guess that'd be how we should use this properly…
			if 'demo' in extra.lower():
				#Keeping the category names consistent with everything else here, though people might like to call it "Demos" or whatever instead and technically there's no reason why we can't do that and this should be an option and I will put this ramble here to remind myself to make it an option eventually
				#TODO How about you put a TODO comment instead
				self.info.categories = ('Trials', )
		
		if main_config.use_original_platform:
			self.info.platform = self.original_platform

		language = self.language		
		if language:
			self.info.languages = [language]

		path = self.path
		if path:
			if path.is_dir():
				icon = look_for_icon_in_folder(Path(path))
				if icon:
					self.info.images['Icon'] = icon
			elif not path.exists():
				logger.warning('Aaaa! %s has non-existent path: %s', self, path)
		else:
			logger.info('Wait what? %s has no path', self)
		#Everything else is gonna be an actual option

class ScummVMLauncher(Launcher):
	def __init__(self, game: ScummVMGame, runner: ConfiguredRunner) -> None:
		self.game: ScummVMGame = game
		super().__init__(game, runner)

	@property
	def game_id(self) -> str:
		return self.game.game_id

	@property
	def command(self) -> LaunchCommand:
		args = ['-f']
		if main_config.scummvm_config_path != Path('~/.config/scummvm/scummvm.ini').expanduser():
			args.append(f'--config={main_config.scummvm_config_path}')
		args.append(self.game.game_id)
		return LaunchCommand(self.runner.config.exe_path, args)
