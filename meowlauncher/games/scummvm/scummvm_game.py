import os

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.game import Game
from meowlauncher.games.common.pc_common_metadata import \
    look_for_icon_in_folder
from meowlauncher.launcher import LaunchCommand, Launcher
from meowlauncher.runner import Runner
from meowlauncher.util.region_info import get_language_by_short_code

from .scummvm_config import scummvm_config


def format_platform(platform: str) -> str:
	#https://github.com/scummvm/scummvm/blob/master/common/platform.cpp#L28
	return {
		#We'll use the same formatting as in emulated_platforms
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
		'os2': 'OS/2',
		'beos': 'BeOS',
		'ppc': 'PocketPC',
		'megadrive': 'Mega Drive',
		'saturn': 'Saturn',
		'pippin': 'Pippin',
	}.get(platform, platform)

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

	@staticmethod
	def _engine_list_to_use():
		return scummvm_config.scummvm_engines

	def add_metadata(self) -> None:
		self.metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it, but I guess to add that as input_info I'd have to know exactly how many buttons and sticks etc it uses
		self.metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		self.metadata.categories = ['Games'] #Safe to assume this by default
		if self.options.get('gameid') == 'agi-fanmade':
			self.metadata.categories = ['Homebrew']
		#genre/subgenre is _probably_ always point and click adventure, but maybe not? (Plumbers is arguably a visual novel (don't @ me), and there's something about some casino card games in the list of supported games)
		#Would be nice to set things like developer/publisher/year but can't really do that unfortunately
		#Let series and series_index be detected by series_detect
		
		engine_id = self.options.get('engineid')
		self.metadata.specific_info['Engine'] = self._engine_list_to_use().get(engine_id)
		extra = self.options.get('extra')
		if extra:
			self.metadata.specific_info['Version'] = extra #Hmm, I guess that'd be how we should use this properly…
			if 'demo' in extra.lower():
				#Keeping the category names consistent with everything else here, though people might like to call it "Demos" or whatever instead and technically there's no reason why we can't do that and this should be an option and I will put this ramble here to remind myself to make it an option eventually
				self.metadata.categories = ['Trials']
		
		if main_config.use_original_platform:
			platform = self.options.get('platform')
			if platform:
				self.metadata.platform = format_platform(platform)
			if platform == 'amiga' and extra == 'CD32':
				self.metadata.platform = 'Amiga CD32'
		
		language_code = self.options.get('language')
		if language_code:
			if language_code == 'br':
				language = get_language_by_short_code('Pt-Br')
			elif language_code == 'se':
				#…That's the region code for Sweden, not the language code for Swedish, so that's odd but that's how it ends up being
				language = get_language_by_short_code('Sv')
			else:
				language = get_language_by_short_code(language_code, case_insensitive=True)
			if language:
				self.metadata.languages = [language]

		path = self.options.get('path')
		if path:
			if os.path.isdir(path):
				icon = look_for_icon_in_folder(path)
				if icon:
					self.metadata.images['Icon'] = icon
			else:
				if main_config.debug:
					print('Aaaa!', self.name, self.game_id, path, 'does not exist')
		else:
			if main_config.debug:
				print('Wait what?', self.name, self.game_id, 'has no path')
		#Everything else is gonna be an actual option

class ScummVMLauncher(Launcher):
	def __init__(self, game: ScummVMGame, runner: Runner) -> None:
		self.game: ScummVMGame = game
		super().__init__(game, runner)

	@property
	def game_id(self) -> str:
		return self.game.game_id

	@property
	def game_type(self) -> str:
		return 'ScummVM'

	def get_launch_command(self) -> LaunchCommand:
		args = ['-f']
		if main_config.scummvm_config_path != os.path.expanduser('~/.config/scummvm/scummvm.ini'):
			args.append(f'--config={main_config.scummvm_config_path}')
		args.append(self.game.game_id)
		return LaunchCommand('scummvm', args)
