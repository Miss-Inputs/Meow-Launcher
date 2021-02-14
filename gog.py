#!/usr/bin/env python3

import copy
import datetime
import json
import os
import shlex
import time
from pathlib import Path

import launchers
import pc_common_metadata
from common_types import MediaType
from config.main_config import main_config
from info import region_info
from metadata import Metadata
from pc_common_metadata import (get_icon_inside_exe,
                                is_probably_different_mode,
                                is_probably_related_tool)


class GOGGameInfo():
	#File named "gameinfo" for Linux games
	def __init__(self, path):
		self.name = None
		self.version = None
		self.dev_version = None
		#Sometimes games only have those 3
		self.language = None
		self.gameid = None
		#GameID is duplicated, and then there's some other ID?
		with open(path, 'rt') as f:
			lines = f.read().splitlines()
			try:
				self.name = lines[0]
				self.version = lines[1]
				self.dev_version = lines[2] if lines[2] != 'n/a' else None
				self.language = lines[3]
				self.gameid = lines[4]
			except IndexError:
				pass

def find_subpath_case_insensitive(path, subpath):
	#We will need this because Windows (or rather NTFS) does not respect case sensitivity, and so sometimes a file will be referred to that has unexpected capitalisation (e.g. playTask referring to blah.EXE when on disk it is .exe)
	#Assumes path is fine and normal
	alleged_path = os.path.join(path, subpath)
	if os.path.exists(alleged_path):
		return alleged_path
	
	parts = Path(subpath).parts
	first_part_lower = parts[0].lower()
	for sub in os.listdir(path):
		maybe_real_path = os.path.join(path, sub)
		if sub.lower() == first_part_lower:
			if len(parts) == 1:
				return maybe_real_path
			return find_subpath_case_insensitive(maybe_real_path, os.path.join(*parts[1:]))

	return None

class GOGTask():
	def __init__(self, json_object):
		self.is_primary = json_object.get('isPrimary', False)
		self.task_type = json_object.get('type') #Just FileTask or URLTask?
		self.path = json_object.get('path') #I guess this is also only for FileTask
		if self.path:
			self.path = self.path.replace('\\', os.path.sep)
		self.working_directory = json_object.get('workingDir') #This would only matter for FileTask I guess
		if self.working_directory:
			self.working_directory = self.working_directory.replace('\\', os.path.sep)
		self.category = json_object.get('category') #"game", "tool", "document"
		args = json_object.get('arguments')
		if args:
			self.args = shlex.split(args) #We don't need to convert backslashes here because the wine'd executable uses them
		else:
			self.args = []
		#languages: Language codes (without dialect eg just "en"), but seems to be ['*'] most of the time
		self.name = json_object.get('name') #Might not be provided if it is the primary task
		self.is_hidden = json_object.get('isHidden', False)
		compatFlags = json_object.get('compatibilityFlags', '')
		if compatFlags:
			self.compatibility_flags = compatFlags.split(' ') #These seem to be those from https://docs.microsoft.com/en-us/windows/deployment/planning/compatibility-fixes-for-windows-8-windows-7-and-windows-vista (but not always case sensitive?), probably important but I'm not sure what to do about them for now
		else:
			self.compatibility_flags = []
		#osBitness: As in GOGJSONGameInfo
		self.link = json_object.get('link') #For URLTask
		#icon: More specific icon I guess, but this can be an exe or DLL to annoy me

	@property
	def is_probably_subtask(self):
		if self.is_primary:
			return False

		if self.category == 'tool' or is_probably_related_tool(self.name) or is_probably_related_tool(self.path) or is_probably_different_mode(self.name) or is_probably_different_mode(self.path):
			return True

		return False

	@property
	def is_dosbox(self):
		if not self.path or not self.working_directory:
			return False
		return self.path.lower() == 'dosbox/dosbox.exe' and self.working_directory.lower() == 'dosbox' and self.task_type == 'FileTask'

	@property
	def is_scummvm(self):
		if not self.path or not self.working_directory:
			return False
		return self.path.lower() == 'scummvm/scummvm.exe' and self.working_directory.lower() == 'scummvm' and self.task_type == 'FileTask'

class GOGJSONGameInfo():
	#File named "gog-<gameid>.info" for Windows games (and sometimes distributed in game folder of Linux games)
	def __init__(self, path):
		with open(path, 'rt') as f:
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
			self.play_tasks = [GOGTask(task_json) for task_json in j.get('playTasks', [])]
			self.support_tasks = [GOGTask(task_json) for task_json in j.get('supportTasks', [])]
			#version: Always 1 if there?
			#osBitness: Array containing '64' as a string rather than just a number like a normal person? I guess we don't need it (unless we care about 32-bit Wine users)
			#overlaySupported: Probably GOG Galaxy related

	@property
	def primary_play_task(self):
		primary_tasks = [task for task in self.play_tasks if task.is_primary]
		if len(primary_tasks) == 1:
			return primary_tasks[0]
		return None #Not sure what happens if more than one has isPrimary tbh, guess it doesn't matter

class GOGGame():
	def __init__(self, game_folder, info, start_script, support_folder):
		self.folder = game_folder
		self.info = info
		self.start_script = start_script
		self.support_folder = support_folder #Is this necessary to pass as an argument? I guess not but I've already found it in look_in_linux_gog_folder
		
		self.name = pc_common_metadata.fix_name(self.info.name)
		self.metadata = Metadata()

	def add_metadata(self):
		icon = self.icon
		if icon:
			self.metadata.images['Icon'] = icon
		self.metadata.specific_info['Version'] = self.info.version
		self.metadata.specific_info['Dev-Version'] = self.info.dev_version
		self.metadata.specific_info['Language-Code'] = self.info.language
		self.metadata.specific_info['GOG-Product-ID'] = self.info.gameid

		self.metadata.platform = 'GOG' if main_config.use_gog_as_platform else 'Linux'
		self.metadata.media_type = MediaType.Digital
		self.metadata.categories = ['Trials'] if self.is_demo else ['Games'] #There are movies on GOG but I'm not sure how they work, no software I think
		#Dang… everything else would require the API, I guess

	@property
	def icon(self):
		for icon_ext in pc_common_metadata.icon_extensions:
			icon_path = os.path.join(self.support_folder, 'icon' + os.extsep + icon_ext)
			if os.path.isfile(icon_path):
				return icon_path
		return None

	@property
	def is_demo(self):
		#The API doesn't even say this for a given product ID, we'll just have to figure it out ourselves
		if self.info.version and 'demo' in self.info.version.lower():
			return True
		if self.info.dev_version and 'demo' in self.info.dev_version.lower():
			return True
		for demo_suffix in pc_common_metadata.demo_suffixes:
			if '({0})'.format(demo_suffix.lower()) in self.name.lower():
				return True
		return False

	def make_launcher(self):
		params = launchers.LaunchParams(self.start_script, [], working_directory=self.folder)
		launchers.make_launcher(params, self.name, self.metadata, 'GOG', self.folder)

class NormalGOGGame(GOGGame):
	def add_metadata(self):
		super().add_metadata()
		game_data_folder = os.path.join(self.folder, 'game')
		engine = pc_common_metadata.try_and_detect_engine_from_folder(game_data_folder)
		if engine:
			self.metadata.specific_info['Engine'] = engine
		for filename in os.listdir(game_data_folder):
			if filename.startswith('goggame-') and filename.endswith('.info'):
				json_info = GOGJSONGameInfo(os.path.join(game_data_folder, filename))
				#This isn't always here, usually this is used for Windows games, but might as well poke at it if it's here
				self.metadata.specific_info['Build-ID'] = json_info.build_id
				self.metadata.specific_info['Client-ID'] = json_info.client_id
				self.metadata.specific_info['GOG-Product-ID'] = json_info.game_id
				lang_name = json_info.language_name
				if lang_name:
					lang = region_info.get_language_by_english_name(lang_name)
					self.metadata.languages.append(lang)
				#We won't do anything special with playTasks, not sure it's completely accurate as it doesn't seem to include arguments to executables where that would be expected (albeit this is in the case of Pushover, which is a DOSBox game hiding as a normal game)
				#Looking at 'category' for the task with 'isPrimary' = true though might be interesting
				break

class DOSBoxGOGGame(GOGGame):
	#TODO: Let user use native DOSBox
	def add_metadata(self):
		super().add_metadata()
		self.metadata.specific_info['Wrapper'] = 'DOSBox'

class ScummVMGOGGame(GOGGame):
	#TODO: Let user use native ScummVM
	def add_metadata(self):
		super().add_metadata()
		self.metadata.specific_info['Wrapper'] = 'ScummVM'

#I think there can be Wine bundled with a game sometimes too?

def look_in_linux_gog_folder(folder):
	gameinfo_path = os.path.join(folder, 'gameinfo')
	if not os.path.isfile(gameinfo_path):
		return None
	gameinfo = GOGGameInfo(gameinfo_path)

	launch_script = os.path.join(folder, 'start.sh')
	if not os.path.isfile(launch_script):
		return None

	#.mojosetup, uninstall-*.sh, docs are also here
	support_folder = os.path.join(folder, 'support')
	if not os.path.isdir(support_folder):
		return None

	if os.path.isdir(os.path.join(folder, 'dosbox')):
		return DOSBoxGOGGame(folder, gameinfo, launch_script, support_folder)
	if os.path.isdir(os.path.join(folder, 'scummvm')):
		return ScummVMGOGGame(folder, gameinfo, launch_script, support_folder)
	if os.path.isdir(os.path.join(folder, 'game')):
		return NormalGOGGame(folder, gameinfo, launch_script, support_folder)

	return None

class WindowsGOGGame():
	def __init__(self, folder, info_file, game_id):
		self.info = GOGJSONGameInfo(info_file)
		self.game_id = game_id
		if game_id != self.info.game_id:
			print('Interesting, in', folder, 'game ID is ', game_id, 'but in the info file it is', self.info.game_id)
		self.folder = folder

		self.original_name = self.info.name
		self.name = pc_common_metadata.fix_name(self.original_name)
		self.metadata = Metadata()

	def add_metadata(self):
		icon = self.icon
		if icon:
			self.metadata.images['Icon'] = icon

		self.metadata.specific_info['GOG-Product-ID'] = self.info.game_id
		lang_name = self.info.language_name
		if lang_name:
			lang = region_info.get_language_by_english_name(lang_name)
			self.metadata.languages.append(lang)

		engine = pc_common_metadata.try_and_detect_engine_from_folder(self.folder)
		if engine:
			self.metadata.specific_info['Engine'] = engine

		self.metadata.platform = 'GOG' if main_config.use_gog_as_platform else 'Windows'
		self.metadata.media_type = MediaType.Digital
		self.metadata.categories = ['Trials'] if self.is_demo else ['Games'] #There are movies on GOG but I'm not sure how they work, no software I think
		#Dang… everything else would require the API, I guess

	@property
	def is_demo(self):
		for demo_suffix in pc_common_metadata.demo_suffixes:
			if '({0})'.format(demo_suffix.lower()) in self.name.lower():
				return True
		return False

	@property
	def icon(self):
		for icon_ext in pc_common_metadata.icon_extensions:
			icon_path = os.path.join(self.folder, 'goggame-' + self.game_id + os.extsep + icon_ext)
			if os.path.isfile(icon_path):
				return icon_path
		return None

	def fix_subfolder_relative_folder(self, folder, subfolder):
		if folder.startswith('..\\'):
			return find_subpath_case_insensitive(self.folder, folder.replace('..\\', ''))
		if folder.startswith('.\\'):
			return find_subpath_case_insensitive(self.folder, folder.replace('.\\', subfolder + os.path.sep))
		return folder

	def get_dosbox_launch_params(self, task):
		args = [self.fix_subfolder_relative_folder(arg, 'dosbox') for arg in task.args]
		dosbox_path = main_config.dosbox_path
		dosbox_folder = find_subpath_case_insensitive(self.folder, 'dosbox') #Game's config files are expecting to be launched from here
		return launchers.LaunchParams(dosbox_path, args, working_directory=dosbox_folder)

	def get_wine_launch_params(self, task):
		if not task.path:
			if main_config.debug:
				print('Oh dear - we cannot deal with tasks that have no path', self.name, task.name, task.args, task.task_type, task.category)
			return None

		if task.path.lower().endswith('.lnk'):
			if main_config.debug:
				print(self.name, 'cannot be launched - we cannot deal with shortcuts right now (we should parse them but I cannot be arsed right now)', self.name, task.name, task.args, task.task_type, task.category)
			return None

		exe_path = find_subpath_case_insensitive(self.folder, task.path)
		working_directory = None
		if task.working_directory:
			working_directory = find_subpath_case_insensitive(self.folder, task.working_directory)
		
		return launchers.get_wine_launch_params(exe_path, task.args, working_directory)

	def get_launcher_params(self, task):
		if main_config.use_system_dosbox and task.is_dosbox:
			return 'DOSBox', self.get_dosbox_launch_params(task)

		#Bruh how we gonna do ScummVM when the .ini file gonna have Windows paths though?
		
		return 'Wine', self.get_wine_launch_params(task)
		
	def make_launcher(self, task):
		emulator_name, params = self.get_launcher_params(task)
		if not params:
			return

		task_metadata = copy.deepcopy(self.metadata)
		if task.category == 'tool':
			task_metadata.categories = ['Applications']
		task_metadata.emulator_name = emulator_name
		task_metadata.specific_info['Compatibility-Flags'] = task.compatibility_flags
		if task.is_dosbox and emulator_name != 'DOSBox':
			task_metadata.specific_info['Wrapper'] = 'DOSBox'
		if task.is_scummvm and emulator_name != 'ScummVM':
			task_metadata.specific_info['Wrapper'] = 'ScummVM'
		task_metadata.specific_info['Executable-Name'] = os.path.basename(task.path)

		if not (task.is_dosbox or task.is_scummvm):
			exe_icon = get_icon_inside_exe(find_subpath_case_insensitive(self.folder, task.path))
			if exe_icon:
				task_metadata.images['Icon'] = exe_icon

		name = self.name
		if task.name:
			if task.is_probably_subtask:
				if task.name.startswith(self.original_name):
					name = task.name.replace(self.original_name, self.name)
				else:
					name += ' ({0})'.format(task.name)
			else:
				name = pc_common_metadata.fix_name(task.name)

		launchers.make_launcher(params, name, task_metadata, 'GOG', self.folder)

	def make_launchers(self):
		actual_tasks = []
		documents = []
		for task in self.info.play_tasks:
			if task.category == 'document':
				documents.append(task)
			#TODO Also names that are not supposed to be launched and are documents: "FAQ", "Manual", "Map of Avernum", "Reference Card"
			elif task.task_type == 'URLTask':
				documents.append(task)
			elif task.is_hidden:
				continue
			else:
				actual_tasks.append(task)
		for task in self.info.support_tasks:
			self.metadata.documents[task.name] = task.link if task.task_type == 'URLTask' else find_subpath_case_insensitive(self.folder, task.path)
		for task in actual_tasks:
			self.make_launcher(task)

def look_in_windows_gog_folder(folder):
	info_file = None
	game_id = None
	for file in os.listdir(folder):
		if file.startswith('goggame-') and file.endswith('.info'):
			info_file = os.path.join(folder, file)
			game_id = file[8:-5]
		#Other files that may exist: goggame-<gameid>.dll, goggame-<gameid>.hashdb (Galaxy related?), goggame-<gameid>.ico, goglog.ini, goggame-galaxyFileList.ini, goggame.sdb, unins000.exe, unins000.dat, unins000.msg
	if not info_file:
		#There are actually instances where this isn't here: Bonus content items (Prisoner of Ice UK version, SOTC Floppy version, etc) but I don't really know what to do with those right now to be quite honest, I guess I could look for "Launch <blah>.lnk" and extract which game to launch from there? But that's weird
		return None
	return WindowsGOGGame(folder, info_file, game_id)

def do_gog_games():
	time_started = time.perf_counter()

	for gog_folder in main_config.gog_folders:
		if not os.path.isdir(gog_folder):
			if main_config.debug:
				print(gog_folder, 'does not exist/is not a directory')
			continue

		for subfolder in os.scandir(gog_folder):
			if not subfolder.is_dir():
				continue
			game = look_in_linux_gog_folder(subfolder.path)
			if not game:
				if main_config.debug:
					print('GOG subfolder does not have a GOG game (detection may have failed)', subfolder.path)

			game.add_metadata()
			game.make_launcher()
	
	if os.path.isfile(main_config.wine_path) or not main_config.wine_path.startswith('/'):
		for windows_gog_folder in main_config.windows_gog_folders:
			if not os.path.isdir(windows_gog_folder):
				if main_config.debug:
					print(windows_gog_folder, 'does not exist/is not a directory')
				continue

			for subfolder in os.scandir(windows_gog_folder):
				if not subfolder.is_dir():
					continue
				game = look_in_windows_gog_folder(subfolder.path)
				if not game:
					if main_config.debug:
						print('GOG subfolder does not have a GOG game (detection may have failed)', subfolder.path)
					continue
				
				game.add_metadata()
				game.make_launchers()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('GOG finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	do_gog_games()
