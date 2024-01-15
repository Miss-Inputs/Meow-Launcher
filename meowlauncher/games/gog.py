"""Classes for GOG game source"""
import copy
import itertools
import json
import logging
import os
import shlex
from abc import ABC
from itertools import chain
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING, Any

from meowlauncher.common_types import MediaType
from meowlauncher.config import main_config
from meowlauncher.exceptions import GameNotSupportedError
from meowlauncher.game import Game
from meowlauncher.games.common import pc_common_info
from meowlauncher.games.common.engine_detect import try_and_detect_engine_from_folder
from meowlauncher.global_runners import Wine
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.launcher import Launcher
from meowlauncher.output.desktop_files import make_launcher
from meowlauncher.util import name_utils, region_info

if TYPE_CHECKING:
	from collections.abc import Mapping, Sequence

	from meowlauncher.game_sources.gog import GOGConfig

logger = logging.getLogger(__name__)


class GameInfoFile:
	"""File named "gameinfo" for Linux GOG games"""

	def __init__(self, path: Path):
		self.name = path.name
		self.version = None
		self.dev_version = None
		# Sometimes games only have those 3
		self.language = None
		self.gameid = None
		# GameID is duplicated, and then there's some other ID?
		with path.open('rt', encoding='utf-8') as f:
			lines = [line.rstrip() for line in itertools.islice(f, 5)]
			try:
				self.name = lines[0]
				self.version = lines[1]
				self.dev_version = lines[2] if lines[2] != 'n/a' else None
				self.language = lines[3]
				self.gameid = lines[4]
			except IndexError:
				pass


class InfoJSONFile:
	"""File named "gog-<gameid>.info" for Windows GOG games (and sometimes distributed in game folder of Linux GOG games)"""

	def __init__(self, path: Path):
		j = json.loads(path.read_bytes())
		self.game_id = j.get('gameId')
		self.build_id = j.get('buildId')
		self.client_id = j.get('clientId')
		# rootGameId: This seems to always be the same as gameId, but maybe there's some cases where it's not? I can only imagine it's something to do with DLC
		# standalone: Usually true or not provided?
		# dependencyGameId: Usually blank?
		self.language_name = j.get(
			'language'
		)  # English name of the language (I guess the default language?)
		# languages: Array of language codes (e.g. en-US)
		self.name = j.get('name')
		self.play_tasks = {Task.get(task_json) for task_json in j.get('playTasks', [])}
		self.support_tasks = {Task.get(task_json) for task_json in j.get('supportTasks', [])}
		# version: Always 1 if there?
		# osBitness: Array containing '64' as a string rather than just a number like a normal person? I guess we don't need it (unless we care about 32-bit Wine users)
		# overlaySupported: Probably GOG Galaxy related

	@property
	def primary_play_task(self) -> 'Task | None':
		primary_tasks = tuple(task for task in self.play_tasks if task.is_primary)
		if len(primary_tasks) == 1:
			primary_task = primary_tasks[0]
			if not isinstance(primary_task, FileTask):
				logger.debug(
					'What the! Turns out you can have primary task as a %s', type(primary_task)
				)
				return None
			return primary_task
		return None  # Not sure what happens if more than one has isPrimary tbh, guess it doesn't matter


class Task:
	""" "task" defined for a Windows GOG game in the gog-blahwhatever.info file under playTasks or supportTasks"""

	def __init__(self, json_object: 'Mapping[str, Any]'):
		self.is_primary: bool = json_object.get('isPrimary', False)
		self.category: str | None = json_object.get('category')  # "game", "tool", "document"

		# languages: Language codes (without dialect eg just "en"), but seems to be ('*', ) most of the time
		self.name: str | None = json_object.get(
			'name'
		)  # Might not be provided if it is the primary task
		self.is_hidden: bool = json_object.get('isHidden', False)
		compatFlags = json_object.get('compatibilityFlags', '')
		self.compatibility_flags = None
		if compatFlags:
			self.compatibility_flags = compatFlags.split(
				' '
			)  # These seem to be those from https://docs.microsoft.com/en-us/windows/deployment/planning/compatibility-fixes-for-windows-8-windows-7-and-windows-vista (but not always case sensitive?), probably important but I'm not sure what to do about them for now
		# osBitness: As in GOGJSONGameInfo
		# icon: More specific icon I guess, but this can be an exe or DLL to annoy me

	@staticmethod
	def get(json_object: 'Mapping[str, Any]') -> 'Task':
		task_type = json_object.get('type')
		if task_type == 'FileTask':
			return FileTask(json_object)
		if task_type == 'URLTask':
			return URLTask(json_object)
		raise AssertionError(f'What the heck? task type is {task_type}')


class FileTask(Task):
	def __init__(self, json_object: 'Mapping[str, Any]'):
		super().__init__(json_object)
		self.path = PureWindowsPath(json_object['path'])
		working_directory: str | None = json_object.get('workingDir')
		self.working_directory = PureWindowsPath(working_directory) if working_directory else None

		self.args: 'Sequence[str]' = ()  # This probably isn't applicable if type = document
		args: str | None = json_object.get('arguments')
		if args:
			self.args = shlex.split(
				args
			)  # We don't need to convert backslashes here because the wine'd executable uses them

	@property
	def is_probably_subtask(self) -> bool:
		"""Tries to guess if this is something like a configuration utility or a different option, not a different game in e.g. a compilation"""
		if self.is_primary:
			return False

		if self.category == 'tool':
			return True
		if name_utils.is_probably_related_tool(self.name) or name_utils.is_probably_different_mode(
			self.name
		):
			return True
		if name_utils.is_probably_related_tool(
			self.path.stem
		) or name_utils.is_probably_different_mode(self.path.stem):
			return True

		return False

	@property
	def is_dosbox(self) -> bool:
		"""Attempts to detect if this task is for launching a bundled DOSBox.
		TODO: This wouldn't work for .info files provided with Linux games"""
		if not self.working_directory:
			return False
		return self.path.name.lower() == 'dosbox.exe' and self.working_directory.stem.lower() in {
			'dosbox',
			'dosbox_windows',
		}

	@property
	def is_scummvm(self) -> bool:
		if not self.working_directory:
			return False
		return (
			self.path.name.lower() == 'scummvm.exe'
			and self.working_directory.stem.lower() == 'scummvm'
		)

	@property
	def is_residualvm(self) -> bool:
		if not self.working_directory:
			return False
		return (
			self.path.name.lower() == 'residualvm.exe'
			and self.working_directory.stem.lower() == 'residualvm'
		)


class URLTask(Task):
	def __init__(self, json_object: 'Mapping[str, Any]'):
		super().__init__(json_object)
		self.link: str = json_object['link']


class GOGGame(Game, ABC):
	"""GOG game natively on Linux, see subclasses NormalGOGGame, DOSBoxGOGGame, ScummVMGOGGame, WineGOGGame"""

	def __init__(
		self,
		game_folder: Path,
		info: GameInfoFile,
		start_script: Path,
		support_folder: Path,
		config: 'GOGConfig',
	):
		super().__init__()
		self.folder = game_folder
		self.info_file = info
		self.start_script = start_script
		self.support_folder = support_folder  # Is this necessary to pass as an argument? I guess not but I've already found it in look_in_linux_gog_folder
		self.config = config

	@property
	def name(self) -> str:
		return name_utils.fix_name(self.info_file.name)

	def add_info(self) -> None:
		icon = self.icon
		if icon:
			self.info.images['Icon'] = icon
		self.info.specific_info['Version'] = self.info_file.version
		self.info.specific_info['Dev Version'] = self.info_file.dev_version
		self.info.specific_info['Language Code'] = self.info_file.language
		self.info.specific_info['GOG Product ID'] = self.info_file.gameid

		self.info.platform = 'GOG' if self.config.use_gog_as_platform else 'Linux'
		self.info.media_type = MediaType.Digital
		self.info.categories = (
			('Trials',) if self.is_demo else ('Games',)
		)  # There are movies on GOG but I'm not sure how they work, no software I think
		# Dang… everything else would require the API, I guess

	@property
	def icon(self) -> Path | None:
		for icon_ext in pc_common_info.icon_extensions:
			icon_path = self.support_folder.joinpath('icon' + os.extsep + icon_ext)
			if icon_path.is_file():
				return icon_path
		return None

	@property
	def is_demo(self) -> bool:
		"""Attempts to guess if this is a demo version and not the full game
		The API doesn't even say this for a given product ID, we'll just have to figure it out ourselves"""
		if self.info_file.version and 'demo' in self.info_file.version.lower():
			return True
		if self.info_file.dev_version and 'demo' in self.info_file.dev_version.lower():
			return True
		return any(
			f'({demo_suffix.lower()})' in self.name.lower()
			for demo_suffix in name_utils.demo_suffixes
		)

	def make_launcher(self) -> None:
		params = LaunchCommand(self.start_script, [], working_directory=self.folder)
		make_launcher(params, self.name, self.info, 'GOG', str(self.folder))


class NormalGOGGame(GOGGame):
	def add_info(self) -> None:
		super().add_info()
		game_data_folder = self.folder.joinpath('game')
		engine = try_and_detect_engine_from_folder(game_data_folder, self.info)
		if engine:
			self.info.specific_info['Engine'] = engine
		# TODO: Should this just be in GOGGame? Is NormalGOGGame a needed class? I guess you don't want to do engine_detect stuff on a DOS/ScummVM game as it takes time and probably won't get anything
		for file in game_data_folder.iterdir():
			if file.name.startswith('goggame-') and file.suffix == '.info':
				json_info = InfoJSONFile(file)
				# This isn't always here, usually this is used for Windows games, but might as well poke at it if it's here
				self.info.specific_info['Build ID'] = json_info.build_id
				self.info.specific_info['Client ID'] = json_info.client_id
				self.info.specific_info['GOG Product ID'] = json_info.game_id
				lang_name = json_info.language_name
				if lang_name:
					lang = region_info.get_language_by_english_name(lang_name)
					if lang:
						self.info.languages = {lang}
				# We won't do anything special with playTasks, not sure it's completely accurate as it doesn't seem to include arguments to executables where that would be expected (albeit this is in the case of Pushover, which is a DOSBox game hiding as a normal game)
				# Looking at 'category' for the task with 'isPrimary' = true though might be interesting
				# TODO: But we totally should though, start_script also could be parsed maybe
				break


class DOSBoxGOGGame(GOGGame):
	"""DOS game that is packaged with DOSBox
	TODO: Let user use native DOSBox"""

	def add_info(self) -> None:
		super().add_info()
		self.info.specific_info['Wrapper'] = 'DOSBox'


class ScummVMGOGGame(GOGGame):
	"""Adventure game that is packaged with ScummVM
	#TODO: Let user use native ScummVM"""

	def add_info(self) -> None:
		super().add_info()
		# TODO: Detect engine from scummvm.ini
		self.info.specific_info['Wrapper'] = 'ScummVM'


class WineGOGGame(GOGGame):
	"""Game from GOG that is packaged as a Linux version, but is a Windows game bundled with Wine
	TODO: Let user use native Wine"""

	def add_info(self) -> None:
		super().add_info()
		self.info.specific_info['Wrapper'] = 'Wine'


class LinuxGOGLauncher(Launcher):
	def __init__(self, game: GOGGame) -> None:
		self.game: GOGGame = game
		super().__init__(game, None)

	@property
	def game_id(self) -> str:
		return str(self.game.folder)

	@property
	def command(self) -> LaunchCommand:
		return LaunchCommand(self.game.start_script, [], working_directory=self.game.folder)


def _find_subpath_case_insensitive(path: Path, subpath: PureWindowsPath) -> Path:
	"""We will need this because Windows (or rather NTFS) does not respect case sensitivity, and so sometimes a file will be referred to that has unexpected capitalisation (e.g. playTask referring to blah.EXE when on disk it is .exe)
	Assumes path is fine and normal"""
	alleged_path = path.joinpath(subpath)
	if alleged_path.exists():
		return alleged_path

	parts = subpath.parts
	first_part_lower = parts[0].lower()
	for sub in path.iterdir():
		if sub.name.lower() == first_part_lower:
			if len(parts) == 1:
				return sub
			return _find_subpath_case_insensitive(sub, PureWindowsPath(*parts[1:]))

	raise FileNotFoundError(alleged_path)


class WindowsGOGGame(Game):
	def __init__(self, folder: Path, info_file: Path, game_id: str, config: 'GOGConfig') -> None:
		super().__init__()
		self.config = config
		self.json_info = InfoJSONFile(info_file)
		self.id_file = None
		id_path = info_file.with_suffix('.id')
		if id_path.is_file():
			self.id_file = json.loads(id_path.read_bytes())

		self.game_id = game_id
		if game_id != self.json_info.game_id:
			logger.debug(
				'Interesting, in %s game ID is %s but in the info file it is %s',
				folder,
				game_id,
				self.json_info.game_id,
			)
		self.folder = folder

		self.original_name = self.json_info.name

	@property
	def name(self) -> str:
		return name_utils.fix_name(self.original_name)

	def add_info(self) -> None:
		icon = self.icon
		if icon:
			self.info.images['Icon'] = icon

		self.info.specific_info['GOG Product ID'] = self.json_info.game_id
		lang_name = self.json_info.language_name
		if lang_name:
			lang = region_info.get_language_by_english_name(lang_name)
			if lang:
				self.info.languages = {lang}

		engine = try_and_detect_engine_from_folder(self.folder, self.info)
		if engine:
			self.info.specific_info['Engine'] = engine

		self.info.platform = 'GOG' if self.config.use_gog_as_platform else 'Windows'
		self.info.media_type = MediaType.Digital
		self.info.categories = (
			('Trials',) if self.is_demo else ('Games',)
		)  # There are movies on GOG but I'm not sure how they work, no software I think
		# Dang… everything else would require the API, I guess

		if self.id_file and not self.info.specific_info.get('Build ID'):
			self.info.specific_info['Build ID'] = self.id_file.get('buildId')

	@property
	def is_demo(self) -> bool:
		"""Guesses if this is a demo based on the name.
		Not sure if there's a better way? I guess looking up the store API"""
		return any(
			f'({demo_suffix.lower()})' in self.name.lower()
			for demo_suffix in name_utils.demo_suffixes
		)

	@property
	def icon(self) -> Path | None:
		for icon_ext in pc_common_info.icon_extensions:
			icon_path = self.folder.joinpath('goggame-' + self.game_id + os.extsep + icon_ext)
			if icon_path.is_file():
				return icon_path
		return None

	def fix_subfolder_relative_folder(
		self, folder: PureWindowsPath, subfolder: PureWindowsPath
	) -> Path:
		"""TODO: ?????? uhhhh does this work how I think it works? I think it's supposed to make DOSBox games work"""
		if folder.is_relative_to('..'):
			return _find_subpath_case_insensitive(self.folder, folder.relative_to('..'))
		return _find_subpath_case_insensitive(self.folder, folder.relative_to(subfolder))

	def get_dosbox_launch_params(self, task: FileTask) -> LaunchCommand:
		args = tuple(
			str(self.fix_subfolder_relative_folder(PureWindowsPath(arg), PureWindowsPath('dosbox')))
			for arg in task.args
			if '\\' in arg
		)
		dosbox_folder = _find_subpath_case_insensitive(
			self.folder, PureWindowsPath('dosbox')
		)  # Game's config files are expecting to be launched from here
		return LaunchCommand(main_config.dosbox_path, args, working_directory=dosbox_folder)

	def get_wine_launch_params(self, task: FileTask) -> LaunchCommand | None:
		# if not task.path:
		# 	logger.info('Oh dear - task %s (%s %s) in %s has no path and we can\'t deal with that right now', task.name, task.args, task.category, self.name)
		# 	return None

		if task.path.suffix.lower() == '.lnk':
			logger.debug(
				self.name,
				'task %s (%s %s %s) in %s cannot be launched - we cannot deal with shortcuts right now (we should parse them but I cannot be arsed right now)',
				task.name,
				task.args,
				task.category,
				self.name,
			)
			return None

		exe_path = _find_subpath_case_insensitive(self.folder, task.path)
		working_directory = None
		if task.working_directory:
			working_directory = PureWindowsPath(
				_find_subpath_case_insensitive(self.folder, task.working_directory)
			)

		wine = Wine()
		if wine.is_available:
			return wine.launch_windows_exe(exe_path, task.args, working_directory)
		raise GameNotSupportedError(f'GOG game {self.name} needs Wine')

	def get_launcher_params(self, task: FileTask) -> tuple[str, LaunchCommand | None]:
		if self.config.use_system_dosbox and task.is_dosbox:
			return 'DOSBox', self.get_dosbox_launch_params(task)

		# Bruh how we gonna do ScummVM when the .ini file gonna have Windows paths though?

		return 'Wine', self.get_wine_launch_params(task)

	def make_launcher(self, task: FileTask) -> None:
		emulator_name, params = self.get_launcher_params(task)
		if not params:
			return

		task_metadata = copy.deepcopy(self.info)
		if task.category == 'tool':
			task_metadata.categories = ('Applications',)
		task_metadata.emulator_name = emulator_name
		if task.compatibility_flags:
			task_metadata.specific_info['Compatibility Flags'] = task.compatibility_flags
		if task.is_dosbox and emulator_name != 'DOSBox':
			task_metadata.specific_info['Wrapper'] = 'DOSBox'
		if task.is_scummvm and emulator_name != 'ScummVM':
			task_metadata.specific_info['Wrapper'] = 'ScummVM'
		if task.is_residualvm and emulator_name != 'ScummVM':
			task_metadata.specific_info['Wrapper'] = 'ResidualVM'
		executable_name = task.path.name
		task_metadata.specific_info['Executable Name'] = executable_name
		if os.path.extsep in executable_name:
			task_metadata.specific_info['Extension'] = executable_name.rsplit(os.path.extsep, 1)[
				-1
			].lower()

		if not (task.is_dosbox or task.is_scummvm or task.is_residualvm):
			exe_path = _find_subpath_case_insensitive(self.folder, task.path)
			exe_icon = pc_common_info.get_icon_inside_exe(exe_path)
			if exe_icon:
				task_metadata.images['Icon'] = exe_icon
			pc_common_info.add_info_for_raw_exe(exe_path, task_metadata)

		name = self.name
		if task.name:
			if task.is_probably_subtask:
				if task.name.startswith(self.original_name):
					name = task.name.replace(self.original_name, self.name)
				else:
					name += f' ({task.name})'
			else:
				name = name_utils.fix_name(task.name)

		make_launcher(params, name, task_metadata, 'GOG', str(self.folder))

	def make_launchers(self) -> None:
		actual_tasks = set()
		documents = set()
		for task in self.json_info.play_tasks:
			if (
				task.category == 'document'
				or (task.name and name_utils.is_probably_documentation(task.name))
				or isinstance(task, URLTask)
			):
				documents.add(task)
			elif task.is_hidden:
				continue
			elif isinstance(task, FileTask):
				actual_tasks.add(task)
		for task in chain(self.json_info.support_tasks, documents):
			if isinstance(task, URLTask):
				self.info.documents[task.name or self.name] = task.link
			elif isinstance(task, FileTask):
				self.info.documents[task.name or self.name] = _find_subpath_case_insensitive(
					self.folder, task.path
				)
		for task in actual_tasks:
			self.make_launcher(task)


class WindowsGOGLauncher(Launcher):
	# TODO
	def __init__(self, game: WindowsGOGGame) -> None:
		self.game: WindowsGOGGame = game
		super().__init__(game, None)

	@property
	def game_id(self) -> str:
		return str(self.game.folder)
