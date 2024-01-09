import copy
import datetime
import gzip
import json
import logging
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from meowlauncher.config import main_config
from meowlauncher.game import Game
from meowlauncher.games.common.engine_detect import detect_engine_recursively
from meowlauncher.games.common.pc_common_info import add_info_for_raw_exe, look_for_icon_for_file
from meowlauncher.info import Date
from meowlauncher.launch_command import LaunchCommand, launch_with_wine
from meowlauncher.output.desktop_files import make_launcher
from meowlauncher.util.name_utils import fix_name

if TYPE_CHECKING:
	from collections.abc import Collection, Iterator, Mapping
	from typing import Any

	from meowlauncher.game_sources.itch_io import ItchioConfig

logger = logging.getLogger(__name__)

__doc__ = """Game source for installed itch.io games (anything installed with the client, and no weird games that use non-recommended install methods) that is not a GameSource yet
TODO: Rework this to be able to optionally just read json, launch all executables in the game dir or whatever, and avoid using butler if preferred
#…But "find any executables in the game dir" is kind of what butler does, albeit with a bit more spicy
#So given we have to filter out butler's detected executables anyway… might as well redo it
#GOG would appreciate a "find likely executables in a folder" function too"""

@lru_cache(maxsize=1)
def _find_butler() -> Path | None:
	"""Sorry we do need this actually, it's a bit assumptiony and hacky to do this but I must
	Do we? For now, maybe"""
	butler_folder = Path('~/.config/itch/broth/butler').expanduser()
	chosen_version = butler_folder.joinpath('.chosen-version')
	try:
		version = chosen_version.read_text(encoding='utf-8')
		return butler_folder.joinpath('versions', version, 'butler')
	except FileNotFoundError:
		return None

def _butler_configure(folder: Path, os_filter: str | None=None, ignore_arch: bool=False) -> 'Mapping[str, Any] | None':
	try:
		butler = _find_butler()
		if not butler:
			return None
		args: list[Path | str] = [butler, '-j', 'configure']
		if os_filter:
			args += ['--os-filter', os_filter]
			if ignore_arch:
				args += ['--arch-filter', '']
		else:
			args.append('--no-filter')
		args.append(folder)
		butler_proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
		j: 'Mapping[str, Any]' = json.loads(butler_proc.stdout.splitlines()[-1])
		return j
	except (subprocess.CalledProcessError, FileNotFoundError):
		return None

def _is_probably_unwanted_candidate(path: Path, all_candidate_basenames: 'Collection[str]') -> bool:
	name = path.name
	if name in {'LinuxPlayer_s.debug', 'UnityPlayer_s.debug'}:
		#Sorry we don't need debug mode go away (also are these just libraries anyway?)
		return True
	if path.suffix == '.dso':
		#This isn't even launchable?
		return True
	if name in {'nacl_helper', 'nacl_helper_bootstrap'}:
		return True
	if len(all_candidate_basenames) == 2 and name == 'nwjc':
		return True
	if len(all_candidate_basenames) == 3 and ('nw' in all_candidate_basenames and 'nwjc' in all_candidate_basenames and name in {'nw', 'nwjc'}):
		return True
	if len(all_candidate_basenames) > 1 and name in {'notification_helper.exe', 'crashpad_handler', 'UnityCrashHandler64.exe', 'winsetup.exe'}:
		return True

	return False

class ItchGame(Game):
	"""Represents a game folder installed by the itch.io client. You probably want .itch/receipt.json.gz to be in there, otherwise this isn't terribly useful"""
	def __init__(self, path: Path, config: 'ItchioConfig') -> None:
		super().__init__()
		self.config = config
		self.path = path
		try:
			with gzip.open(path.joinpath('.itch', 'receipt.json.gz')) as receipt_file:
				self.receipt = json.load(receipt_file)
		except FileNotFoundError:
			self.receipt = None
		self._name = path.name #This will be replaced later; as the folder name is some kind of game-name formatted sort of thing
		self.is_demo = False
		self.platforms: 'Collection[str]' = set()
		self.category = 'game'
		self.game_type = 'default'

	@property
	def name(self) -> str:
		return self._name

	def _add_metadata_from_folder(self) -> None:
		engine = detect_engine_recursively(self.path, self.info)
		if engine:
			self.info.specific_info['Engine'] = engine

	def _add_metadata_from_receipt(self) -> None:
		if not self.receipt:
			return

		game = self.receipt['game']
		upload = self.receipt['upload']
		#build, files, installerName probably not needed

		title = game.get('title')
		if title:
			self._name = fix_name(title)
		self.info.specific_info['Game ID'] = game.get('id')
		self.info.documents['Homepage'] = game.get('url')

		description = game.get('shortText')
		if description:
			self.info.descriptions['Description'] = description

		self.game_type = game.get('type', 'default') #Default, flash, unity, java, html
		self.category = game.get('classification', 'game') #game, tool, assets, game_mod, physical_game, soundtrack, other, comic, book
		created_at = game.get('createdAt')
		published_at = game.get('publishedAt')
		if created_at:
			creation_date = datetime.date.fromisoformat(created_at[:10])
			self.info.specific_info['Creation Date'] = Date(creation_date.year, creation_date.month, creation_date.day)
		if published_at:
			release_date = datetime.date.fromisoformat(published_at[:10])
			self.info.release_date = Date(release_date.year, release_date.month, release_date.day)
		
		#coverUrl, stillCoverUrl might be useful? I dunno
		#platforms is what platforms the game _can_ be available for, but it doesn't tell us about this exe
		#minPrice, canBeBought, sale aren't so useful here as this receipt is generated at the time this game is downloaded I think which might be out of date
		user = game.get('user')
		if user:
			user_name = user.get('displayName')
			#not using the second param of .get here because we also don't want it to be an empty string
			if not user_name:
				user_name = user.get('username')
			if user_name:
				self.info.developer = self.info.publisher = user_name
			#developer and pressUser here just indicate if this user (who has uploaded the game) has ticked a box saying they are a developer or press, which doesn't seem to matter
			self.info.documents['Developer Homepage'] = user.get('url')

		if upload:
			build_name = upload.get('displayName')
			if not build_name:
				build_name = upload.get('filename')
			self.info.specific_info['Build Name'] = build_name
			self.is_demo = upload.get('demo')
			if self.is_demo and not 'demo' in self.name.lower():
				self._name += ' (Demo)'
			self.info.specific_info['Upload Type'] = upload.get('type', 'default') #default, flash, unity, java, html, soundtrack, book, video, documentation, mod, audio_assets, graphical_assets, sourcecode, other
			self.platforms = set(upload.get('platforms', {}).keys()) #I think the values show if it's x86/x64 but eh
			#Not sure what channelName or preorder does
			upload_created_at = upload.get('createdAt')
			upload_updated_at = upload.get('updatedAt')
			if upload_created_at:
				upload_creation_date = datetime.date.fromisoformat(upload_created_at[:10])
				self.info.specific_info['Upload Creation Date'] = Date(upload_creation_date.year, upload_creation_date.month, upload_creation_date.day)
			if upload_updated_at:
				upload_date = datetime.date.fromisoformat(upload_updated_at[:10])
				self.info.specific_info['Upload Date'] = Date(upload_date.year, upload_date.month, upload_date.day)

		#build often is not there, but it has its own user field? The rest is not useful sadly

	def add_info(self) -> None:
		self._add_metadata_from_folder()
		self._add_metadata_from_receipt()
		
		category = 'Games'
		if self.is_demo:
			category = 'Trials'
		elif self.category == 'tool':
			category = 'Applications'
		elif self.category != 'game':
			category = self.category.replace('_', ' ').title()
			
		self.info.categories = [category]

		platform = None
		if self.config.use_itch_io_as_platform:
			platform = 'itch.io'
		elif self.game_type == 'flash':
			platform = 'Flash'
		elif self.game_type == 'java':
			platform = 'Java'
		elif self.game_type == 'html':
			platform = 'HTML'
		else:
			platform = '/'.join('Mac' if plat == 'osx' else plat.title() for plat in self.platforms)
		self.info.specific_info['Game Type'] = self.game_type
		self.info.platform = platform

	def _try_and_find_exe(self, os_filter: str | None=None, no_arch_filter: bool=False) -> 'Iterator[tuple[str | None, Path, Mapping[str, bool] | None]]':
		"""Iterates over candidates for executable: "flavour" (platform), path to executable, and "windowsInfo"
		This is the fun part. There is no info in the receipt that actually tells us what to run, the way the itch.io app does it is use heuristics to figure that out. So if we don't have butler, we'd have to re-implement dash ourselves, which would suck and let's not
		I still kinda want a fallback method that just grabs something ending with .x86 or .sh etc in the folder, though
		#TODO: Yeah we'll need that thanks
		"""
		output = _butler_configure(self.path, os_filter, no_arch_filter)
		if not output:
			#Bugger
			return
		candidates = output['value']['candidates']
		if not candidates:
			return
		#arch, size might also be useful
		#scriptInfo only applies if flavor == script (and just contains interpreter which shouldn't matter), windowsInfo only applies if flavour == windows
		for candidate in candidates:
			yield candidate['flavor'], Path(output['value']['basePath'], candidate['path']), candidate.get('windowsInfo')
		return

	def _make_exe_launcher(self, flavour: str | None, exe_path: Path, windows_info: 'Mapping[str, bool] | None') -> None:
		info = copy.deepcopy(self.info)
		executable_name = exe_path.name
		info.specific_info['Executable Name'] = executable_name
		extension = exe_path.suffix
		if extension:
			info.specific_info['Extension'] = extension[1:].lower()
		info.specific_info['Executable Type'] = flavour
		#This shouldn't really happen, but sometimes the platform field in upload in the receipt is inaccurate
		#Pretend Mac doesn't exist
		if not flavour:
			logger.info('dang %s is not in flavourtown') #I don't think this happens
			return
		if flavour in {'script', 'linux'}:
			info.platform = 'Linux'
		elif flavour.startswith('windows'):
			info.platform = 'Windows'
		elif flavour == 'jar':
			info.platform = 'Java' #That will do
		elif flavour == 'html':
			info.platform = 'HTML'
		elif flavour == 'love':
			info.platform = 'LOVE'

		if exe_path.is_file():
			#Might be a folder if Mac, I guess
			#Although we ignore that
			add_info_for_raw_exe(exe_path, self.info)
			if 'icon' not in info.images:
				icon = look_for_icon_for_file(exe_path)
				if icon:
					info.images['Icon'] = icon

		params = get_launch_params(flavour, exe_path, windows_info)
		if not params:
			if flavour not in {'app-macos', 'macos'}:
				logger.debug('Not dealing with %s %s %s %s %s at this point in time', self.path, flavour, exe_path, self.platforms, self.info.platform)
			return
		if params[1]:
			info.emulator_name = params[1]

		make_launcher(params[0], self.name, info, 'itch.io', str(self.path))

	def make_launcher(self) -> None:
		os_filter = None
		if 'linux' in self.platforms:
			os_filter = 'linux'
		elif 'windows' in self.platforms:
			os_filter = 'windows'

		candidates = set(self._try_and_find_exe(os_filter))
		if not candidates:
			candidates = set(self._try_and_find_exe())

		if not candidates:
			#Warning and not info, because it's effectively telling you the game cannot be launched
			logger.warning('No launch candidates found for %s')
			return

		candidate_basenames = {path.name for _, path, _ in candidates}

		for flavour, path, windows_info in candidates:
			if _is_probably_unwanted_candidate(path, candidate_basenames):
				continue
			self._make_exe_launcher(flavour, path, windows_info)

def get_launch_params(flavour: str, exe_path: Path, windows_info: 'Mapping[str, bool] | None') -> tuple[LaunchCommand, str | None] | None:
	if flavour in {'linux', 'script'}:
		#ez pez
		return LaunchCommand(exe_path, []), None
	if flavour == 'html':
		#hmm I guess this will do
		return LaunchCommand(Path('xdg-open'), [str(exe_path)]), None
	if flavour in {'windows', 'windows-script'}:
		if windows_info and windows_info.get('dotNet', False):
			#Mono does not really count as an emulator but whateves (I mean neither does Wine by the name but for metadata purposes I will)
			return LaunchCommand(Path('mono'), [str(exe_path)]), 'Mono'
		#gui might also be useful, if it is false then run in terminal?
		return launch_with_wine(main_config.wine_path, main_config.wineprefix, exe_path, []), 'Wine'
	if flavour == 'jar':
		#Guess we can just assume it's installed who cares
		#TODO: I care!
		return LaunchCommand(Path('java'), ['-jar', str(exe_path)]), None
	if flavour == 'love':
		#Guess we can also just assume this is installed who cares
		#TODO: Grrrrrr
		return LaunchCommand(Path('love'), [str(exe_path)]), 'LOVE'

	return None
	
