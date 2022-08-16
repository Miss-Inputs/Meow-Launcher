import copy
import json
import os
import shlex
from abc import ABC
from collections.abc import Mapping, Sequence
from itertools import chain
from pathlib import Path, PureWindowsPath
from typing import Any, Optional

from meowlauncher.common_types import MediaType
from meowlauncher.config.main_config import main_config
from meowlauncher.configured_runner import ConfiguredRunner
from meowlauncher.game import Game
from meowlauncher.games.common import pc_common_metadata
from meowlauncher.games.common.engine_detect import \
    try_and_detect_engine_from_folder
from meowlauncher.launch_command import LaunchCommand, launch_with_wine
from meowlauncher.launcher import Launcher
from meowlauncher.output.desktop_files import make_launcher
from meowlauncher.util import name_utils, region_info


class GOGGameInfo():
	#File named "gameinfo" for Linux games
	def __init__(self, path: Path):
		self.name = path.name
		self.version = None
		self.dev_version = None
		#Sometimes games only have those 3
		self.language = None
		self.gameid = None
		#GameID is duplicated, and then there's some other ID?
		with path.open('rt', encoding='utf-8') as f:
			lines = f.readlines(5)
			try:
				self.name = lines[0]
				self.version = lines[1]
				self.dev_version = lines[2] if lines[2] != 'n/a' else None
				self.language = lines[3]
				self.gameid = lines[4]
			except IndexError:
				pass

class GOGJSONGameInfo():
	#File named "gog-<gameid>.info" for Windows games (and sometimes distributed in game folder of Linux games)
	def __init__(self, path: Path):
		with path.open('rt', encoding='utf-8') as f:
			j = json.load(f)
			self.game_id = j.get('gameId')
			self.build_id = j.get('buildId')
			self.client_id = j.get('clientId')
			#rootGameId: This seems to always be the same as gameId, but maybe there's some cases where it's not? I can only imagine it's something to do with DLC
			#standalone: Usually true or not provided?
			#dependencyGameId: Usually blank?
			self.language_name = j.get('language') #English name of the language (I guess the default language?)
			#languages: Array of language codes (e.g. en-US)
			self.name = j.get('name')
			self.play_tasks = tuple(GOGTask(task_json) for task_json in j.get('playTasks', []))
			self.support_tasks = {GOGTask(task_json) for task_json in j.get('supportTasks', [])}
			#version: Always 1 if there?
			#osBitness: Array containing '64' as a string rather than just a number like a normal person? I guess we don't need it (unless we care about 32-bit Wine users)
			#overlaySupported: Probably GOG Galaxy related

	@property
	def primary_play_task(self) -> Optional['GOGTask']:
		primary_tasks = tuple(task for task in self.play_tasks if task.is_primary)
		if len(primary_tasks) == 1:
			return primary_tasks[0]
		return None #Not sure what happens if more than one has isPrimary tbh, guess it doesn't matter

class GOGTask():
	def __init__(self, json_object: Mapping[str, Any]):
		self.is_primary: bool = json_object.get('isPrimary', False)
		self.task_type: Optional[str] = json_object.get('type') #Just FileTask or URLTask?
		path: Optional[str] = json_object.get('path') #I guess this is also only for FileTask
		self.path = path.replace('\\', os.path.sep) if path else None #TODO: Should use pathlib.Path, is this relative? Do we need to do something weird? I guess it could be URL if URLTask?
		self.working_directory: Optional[str] = json_object.get('workingDir') #This would only matter for FileTask I guess
		if self.working_directory:
			self.working_directory = self.working_directory.replace('\\', os.path.sep)
		self.category: Optional[str] = json_object.get('category') #"game", "tool", "document"

		self.args: Sequence[str] = ()
		args: Optional[str] = json_object.get('arguments')
		if args:
			self.args = shlex.split(args) #We don't need to convert backslashes here because the wine'd executable uses them

		#languages: Language codes (without dialect eg just "en"), but seems to be ('*', ) most of the time
		self.name: Optional[str] = json_object.get('name') #Might not be provided if it is the primary task
		self.is_hidden: bool = json_object.get('isHidden', False)
		compatFlags = json_object.get('compatibilityFlags', '')
		self.compatibility_flags = None
		if compatFlags:
			self.compatibility_flags = compatFlags.split(' ') #These seem to be those from https://docs.microsoft.com/en-us/windows/deployment/planning/compatibility-fixes-for-windows-8-windows-7-and-windows-vista (but not always case sensitive?), probably important but I'm not sure what to do about them for now
		#osBitness: As in GOGJSONGameInfo
		self.link: Optional[str] = json_object.get('link') #For URLTask
		#icon: More specific icon I guess, but this can be an exe or DLL to annoy me

	@property
	def is_probably_subtask(self) -> bool:
		if self.is_primary:
			return False

		if self.category == 'tool' or name_utils.is_probably_related_tool(self.name) or name_utils.is_probably_related_tool(self.path) or name_utils.is_probably_different_mode(self.name) or name_utils.is_probably_different_mode(self.path):
			return True

		return False

	@property
	def is_dosbox(self) -> bool:
		if not self.path or not self.working_directory:
			return False
		return os.path.basename(self.path.lower()) == 'dosbox.exe' and self.working_directory.lower().rstrip('/') in {'dosbox', 'dosbox_windows'} and self.task_type == 'FileTask'

	@property
	def is_scummvm(self) -> bool:
		if not self.path or not self.working_directory:
			return False
		return self.path.lower() == 'scummvm/scummvm.exe' and self.working_directory.lower() == 'scummvm' and self.task_type == 'FileTask'

	@property
	def is_residualvm(self) -> bool:
		if not self.path or not self.working_directory:
			return False
		return self.path.lower() == 'residualvm/residualvm.exe' and self.working_directory.lower() == 'residualvm' and self.task_type == 'FileTask'

class GOGGame(Game, ABC):
	def __init__(self, game_folder: Path, info: GOGGameInfo, start_script: Path, support_folder: Path):
		super().__init__()
		self.folder = game_folder
		self.info = info
		self.start_script = start_script
		self.support_folder = support_folder #Is this necessary to pass as an argument? I guess not but I've already found it in look_in_linux_gog_folder

	@property
	def name(self) -> str:
		return name_utils.fix_name(self.info.name)

	def add_metadata(self) -> None:
		icon = self.icon
		if icon:
			self.metadata.images['Icon'] = icon
		self.metadata.specific_info['Version'] = self.info.version
		self.metadata.specific_info['Dev Version'] = self.info.dev_version
		self.metadata.specific_info['Language Code'] = self.info.language
		self.metadata.specific_info['GOG Product ID'] = self.info.gameid

		self.metadata.platform = 'GOG' if main_config.use_gog_as_platform else 'Linux'
		self.metadata.media_type = MediaType.Digital
		self.metadata.categories = ('Trials', ) if self.is_demo else ('Games', ) #There are movies on GOG but I'm not sure how they work, no software I think
		#Dang… everything else would require the API, I guess

	@property
	def icon(self) -> Optional[Path]:
		for icon_ext in pc_common_metadata.icon_extensions:
			icon_path = self.support_folder.joinpath('icon' + os.extsep + icon_ext)
			if icon_path.is_file():
				return icon_path
		return None

	@property
	def is_demo(self) -> bool:
		#The API doesn't even say this for a given product ID, we'll just have to figure it out ourselves
		if self.info.version and 'demo' in self.info.version.lower():
			return True
		if self.info.dev_version and 'demo' in self.info.dev_version.lower():
			return True
		return any(f'({demo_suffix.lower()})' in self.name.lower() for demo_suffix in name_utils.demo_suffixes)
		
	def make_launcher(self) -> None:
		params = LaunchCommand(str(self.start_script), [], working_directory=str(self.folder))
		make_launcher(params, self.name, self.metadata, 'GOG', str(self.folder))

class NormalGOGGame(GOGGame):
	def add_metadata(self) -> None:
		super().add_metadata()
		game_data_folder = self.folder.joinpath('game')
		engine = try_and_detect_engine_from_folder(game_data_folder, self.metadata)
		if engine:
			self.metadata.specific_info['Engine'] = engine
		#TODO: Should this just be in GOGGame? Is NormalGOGGame a needed class? I guess you don't want to do engine_detect stuff on a DOS/ScummVM game as it takes time and probably won't get anything
		for file in game_data_folder.iterdir():
			if file.name.startswith('goggame-') and file.suffix == '.info':
				json_info = GOGJSONGameInfo(file)
				#This isn't always here, usually this is used for Windows games, but might as well poke at it if it's here
				self.metadata.specific_info['Build ID'] = json_info.build_id
				self.metadata.specific_info['Client ID'] = json_info.client_id
				self.metadata.specific_info['GOG Product ID'] = json_info.game_id
				lang_name = json_info.language_name
				if lang_name:
					lang = region_info.get_language_by_english_name(lang_name)
					if lang:
						self.metadata.languages = {lang}
				#We won't do anything special with playTasks, not sure it's completely accurate as it doesn't seem to include arguments to executables where that would be expected (albeit this is in the case of Pushover, which is a DOSBox game hiding as a normal game)
				#Looking at 'category' for the task with 'isPrimary' = true though might be interesting
				#TODO: But we totally should though, start_script also could be parsed maybe
				break

class DOSBoxGOGGame(GOGGame):
	#TODO: Let user use native DOSBox
	def add_metadata(self) -> None:
		super().add_metadata()
		self.metadata.specific_info['Wrapper'] = 'DOSBox'

class ScummVMGOGGame(GOGGame):
	#TODO: Let user use native ScummVM
	def add_metadata(self) -> None:
		super().add_metadata()
		#TODO: Detect engine from scummvm.ini
		self.metadata.specific_info['Wrapper'] = 'ScummVM'

#I think there can be Wine bundled with a game sometimes too?

class LinuxGOGLauncher(Launcher):
	def __init__(self, game: GOGGame, runner: ConfiguredRunner) -> None:
		self.game: GOGGame = game
		super().__init__(game, runner)

	@property
	def game_type(self) -> str:
		return 'GOG'
	
	@property
	def game_id(self) -> str:
		return str(self.game.folder)

	@property
	def command(self) -> LaunchCommand:
		return LaunchCommand(str(self.game.start_script), [], working_directory=str(self.game.folder))

def _find_subpath_case_insensitive(path: Path, subpath: str) -> Path:
	#We will need this because Windows (or rather NTFS) does not respect case sensitivity, and so sometimes a file will be referred to that has unexpected capitalisation (e.g. playTask referring to blah.EXE when on disk it is .exe)
	#Assumes path is fine and normal
	alleged_path = path.joinpath(subpath)
	if alleged_path.exists():
		return alleged_path
	
	#TODO: Can I rewrite this to not use str? I'm confused right now
	#TODO: Can subpath just be a pure Windows (relative) path?
	parts = PureWindowsPath(subpath).parts
	first_part_lower = parts[0].lower()
	for sub in path.iterdir():
		if sub.name.lower() == first_part_lower:
			if len(parts) == 1:
				return sub
			return _find_subpath_case_insensitive(sub, str(PureWindowsPath(*parts[1:])))

	raise FileNotFoundError(alleged_path)

class WindowsGOGGame(Game):
	def __init__(self, folder: Path, info_file: Path, game_id: str) -> None:
		super().__init__()
		self.info = GOGJSONGameInfo(info_file)
		self.id_file = None
		id_path = info_file.with_suffix('.id')
		if id_path.is_file():
			with id_path.open('rb') as id_file:
				self.id_file = json.load(id_file)

		self.game_id = game_id
		if game_id != self.info.game_id:
			print('Interesting, in', folder, 'game ID is ', game_id, 'but in the info file it is', self.info.game_id)
		self.folder = folder

		self.original_name = self.info.name

	@property
	def name(self) -> str:
		return name_utils.fix_name(self.original_name)

	def add_metadata(self) -> None:
		icon = self.icon
		if icon:
			self.metadata.images['Icon'] = icon

		self.metadata.specific_info['GOG Product ID'] = self.info.game_id
		lang_name = self.info.language_name
		if lang_name:
			lang = region_info.get_language_by_english_name(lang_name)
			if lang:
				self.metadata.languages = {lang}

		engine = try_and_detect_engine_from_folder(self.folder, self.metadata)
		if engine:
			self.metadata.specific_info['Engine'] = engine

		self.metadata.platform = 'GOG' if main_config.use_gog_as_platform else 'Windows'
		self.metadata.media_type = MediaType.Digital
		self.metadata.categories = ('Trials', ) if self.is_demo else ('Games', ) #There are movies on GOG but I'm not sure how they work, no software I think
		#Dang… everything else would require the API, I guess

		if self.id_file and not self.metadata.specific_info.get('Build ID'):
			self.metadata.specific_info['Build ID'] = self.id_file.get('buildId')

	@property
	def is_demo(self) -> bool:
		return any(f'({demo_suffix.lower()})' in self.name.lower() for demo_suffix in name_utils.demo_suffixes)

	@property
	def icon(self) -> Optional[Path]:
		for icon_ext in pc_common_metadata.icon_extensions:
			icon_path = self.folder.joinpath('goggame-' + self.game_id + os.extsep + icon_ext)
			if icon_path.is_file():
				return icon_path
		return None

	def fix_subfolder_relative_folder(self, folder: str, subfolder: str) -> str:
		#TODO: This should probs use pathlib.Path too?
		if folder.startswith('..\\'):
			return str(_find_subpath_case_insensitive(self.folder, folder.replace('..\\', '')))
		if folder.startswith('.\\'):
			return str(_find_subpath_case_insensitive(self.folder, folder.replace('.\\', subfolder + os.path.sep)))
		return folder

	def get_dosbox_launch_params(self, task: GOGTask) -> LaunchCommand:
		args = tuple(self.fix_subfolder_relative_folder(arg, 'dosbox') for arg in task.args)
		dosbox_path = main_config.dosbox_path
		dosbox_folder = _find_subpath_case_insensitive(self.folder, 'dosbox') #Game's config files are expecting to be launched from here
		return LaunchCommand(dosbox_path, args, working_directory=str(dosbox_folder))

	def get_wine_launch_params(self, task: GOGTask) -> Optional[LaunchCommand]:
		if not task.path:
			if main_config.debug:
				print('Oh dear - we cannot deal with tasks that have no path', self.name, task.name, task.args, task.task_type, task.category)
			return None

		if task.path.lower().endswith('.lnk'):
			if main_config.debug:
				print(self.name, 'cannot be launched - we cannot deal with shortcuts right now (we should parse them but I cannot be arsed right now)', self.name, task.name, task.args, task.task_type, task.category)
			return None

		exe_path = _find_subpath_case_insensitive(self.folder, task.path)
		working_directory = None
		if task.working_directory:
			working_directory = _find_subpath_case_insensitive(self.folder, task.working_directory)
		
		return launch_with_wine(main_config.wine_path, main_config.wineprefix, str(exe_path), task.args, str(working_directory))

	def get_launcher_params(self, task: GOGTask) -> tuple[str, Optional[LaunchCommand]]:
		if main_config.use_system_dosbox and task.is_dosbox:
			return 'DOSBox', self.get_dosbox_launch_params(task)

		#Bruh how we gonna do ScummVM when the .ini file gonna have Windows paths though?
		
		return 'Wine', self.get_wine_launch_params(task)
		
	def make_launcher(self, task: GOGTask) -> None:
		emulator_name, params = self.get_launcher_params(task)
		if not params:
			return
		if not task.path: #It already won't be, just satisfying automated code checkers
			return
		
		task_metadata = copy.deepcopy(self.metadata)
		if task.category == 'tool':
			task_metadata.categories = ('Applications', )
		task_metadata.emulator_name = emulator_name
		if task.compatibility_flags:
			task_metadata.specific_info['Compatibility Flags'] = task.compatibility_flags
		if task.is_dosbox and emulator_name != 'DOSBox':
			task_metadata.specific_info['Wrapper'] = 'DOSBox'
		if task.is_scummvm and emulator_name != 'ScummVM':
			task_metadata.specific_info['Wrapper'] = 'ScummVM'
		if task.is_residualvm and emulator_name != 'ScummVM':
			task_metadata.specific_info['Wrapper'] = 'ResidualVM'
		executable_name = os.path.basename(task.path)
		task_metadata.specific_info['Executable Name'] = executable_name
		if os.path.extsep in executable_name:
			task_metadata.specific_info['Extension'] = executable_name.rsplit(os.path.extsep, 1)[-1].lower()

		if not (task.is_dosbox or task.is_scummvm or task.is_residualvm):
			exe_path = _find_subpath_case_insensitive(self.folder, task.path)
			exe_icon = pc_common_metadata.get_icon_inside_exe(str(exe_path))
			if exe_icon:
				task_metadata.images['Icon'] = exe_icon
			pc_common_metadata.add_metadata_for_raw_exe(str(exe_path), task_metadata)

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
		for task in self.info.play_tasks:
			if task.category == 'document':
				documents.add(task)
			elif task.name and name_utils.is_probably_documentation(task.name):
				documents.add(task)
			elif task.task_type == 'URLTask':
				documents.add(task)
			elif task.is_hidden:
				continue
			else:
				actual_tasks.add(task)
		for task in chain(self.info.support_tasks, documents):
			self.metadata.documents[task.name] = task.link if task.task_type == 'URLTask' else _find_subpath_case_insensitive(self.folder, task.path)
		for task in actual_tasks:
			self.make_launcher(task)
