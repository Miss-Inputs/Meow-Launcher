import copy
import datetime
import gzip
import json
import os
import subprocess

from meowlauncher import desktop_launchers, launcher
from meowlauncher.config.main_config import main_config
from meowlauncher.games.common.engine_detect import detect_engine_recursively
from meowlauncher.games.common.name_utils import fix_name
from meowlauncher.games.common.pc_common_metadata import (
    add_metadata_for_raw_exe, look_for_icon_next_to_file)
from meowlauncher.metadata import Date, Metadata

#TODO: Rework this to be able to optionally just read json, launch all executables in the game dir or whatever, and avoid using butler if preferred

def find_butler():
	#Sorry we do need this actually, it's a bit assumptiony and hacky to do this but I must
	butler_folder = os.path.expanduser('~/.config/itch/broth/butler')
	chosen_version = os.path.join(butler_folder, '.chosen-version')
	try:
		with open(chosen_version, 'rt') as f:
			version = f.read()
			return os.path.join(butler_folder, 'versions', version, 'butler')
	except FileNotFoundError:
		return None

def butler_configure(folder, os_filter=None, ignore_arch=False):
	if not hasattr(butler_configure, 'butler_path'):
		butler_configure.butler_path = find_butler()
	if not butler_configure.butler_path:
		return None
	try:
		args = [butler_configure.butler_path, '-j', 'configure']
		if os_filter:
			args += ['--os-filter', os_filter]
			if ignore_arch:
				args += ['--arch-filter', '']
		else:
			args.append('--no-filter')
		args.append(folder)
		butler_proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
		return json.loads(butler_proc.stdout.splitlines()[-1])
	except (subprocess.CalledProcessError, FileNotFoundError):
		return None

def is_probably_unwanted_candidate(path, all_candidate_basenames):
	name = os.path.basename(path)
	if name in ('LinuxPlayer_s.debug', 'UnityPlayer_s.debug'):
		#Sorry we don't need debug mode go away (also are these just libraries anyway?)
		return True
	if path.endswith('.dso'):
		#This isn't even launchable?
		return True
	if name in ('nacl_helper', 'nacl_helper_bootstrap'):
		return True
	if (len(all_candidate_basenames) == 2 and name == 'nwjc') or (len(all_candidate_basenames) == 3 and ('nw' in all_candidate_basenames and 'nwjc' in all_candidate_basenames and name in ('nw', 'nwjc'))):
		return True
	if len(all_candidate_basenames) > 1 and name in ('notification_helper.exe', 'crashpad_handler', 'UnityCrashHandler64.exe', 'winsetup.exe'):
		return True

	return False

class ItchGame():
	def __init__(self, path):
		self.path = path
		try:
			with gzip.open(os.path.join(path, '.itch', 'receipt.json.gz')) as receipt_file:
				self.receipt = json.load(receipt_file)
		except FileNotFoundError:
			self.receipt = None
		self.metadata = Metadata()
		self.name = os.path.basename(path) #This will be replaced later
		self.is_demo = False
		self.platforms = []
		self.category = 'game'
		self.game_type = 'default'

	def add_metadata_from_folder(self):
		engine = detect_engine_recursively(self.path, self.metadata)
		if engine:
			self.metadata.specific_info['Engine'] = engine

	def add_metadata_from_receipt(self):
		if not self.receipt:
			return

		game = self.receipt['game']
		upload = self.receipt['upload']
		#build, files, installerName probably not needed

		title = game.get('title')
		if title:
			self.name = fix_name(title)
		self.metadata.specific_info['Game-ID'] = game.get('id')
		self.metadata.documents['Homepage'] = game.get('url')

		description = game.get('shortText')
		if description:
			self.metadata.descriptions['Description'] = description

		self.game_type = game.get('type', 'default') #Default, flash, unity, java, html
		self.category = game.get('classification', 'game') #game, tool, assets, game_mod, physical_game, soundtrack, other, comic, book
		created_at = game.get('createdAt')
		published_at = game.get('publishedAt')
		if created_at:
			creation_date = datetime.date.fromisoformat(created_at[:10])
			self.metadata.specific_info['Creation-Date'] = Date(creation_date.year, creation_date.month, creation_date.day)
		if published_at:
			release_date = datetime.date.fromisoformat(published_at[:10])
			self.metadata.release_date = Date(release_date.year, release_date.month, release_date.day)
		
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
				self.metadata.developer = self.metadata.publisher = user_name
			#developer and pressUser here just indicate if this user (who has uploaded the game) has ticked a box saying they are a developer or press, which doesn't seem to matter
			self.metadata.documents['Developer-Homepage'] = user.get('url')

		if upload:
			build_name = upload.get('displayName')
			if not build_name:
				build_name = upload.get('filename')
			self.metadata.specific_info['Build-Name'] = build_name
			self.is_demo = upload.get('demo')
			if self.is_demo and not 'demo' in self.name.lower():
				self.name += ' (Demo)'
			self.metadata.specific_info['Upload-Type'] = upload.get('type', 'default') #default, flash, unity, java, html, soundtrack, book, video, documentation, mod, audio_assets, graphical_assets, sourcecode, other
			self.platforms = list(upload.get('platforms', {}).keys()) #I think the values show if it's x86/x64 but eh
			#Not sure what channelName or preorder does
			upload_created_at = upload.get('createdAt')
			upload_updated_at = upload.get('updatedAt')
			if upload_created_at:
				upload_creation_date = datetime.date.fromisoformat(upload_created_at[:10])
				self.metadata.specific_info['Upload-Creation-Date'] = Date(upload_creation_date.year, upload_creation_date.month, upload_creation_date.day)
			if upload_updated_at:
				upload_date = datetime.date.fromisoformat(upload_updated_at[:10])
				self.metadata.specific_info['Upload-Date'] = Date(upload_date.year, upload_date.month, upload_date.day)

		#build often is not there, but it has its own user field? The rest is not useful sadly

	def add_metadata(self):
		self.add_metadata_from_folder()
		self.add_metadata_from_receipt()
		
		category = 'Games'
		if self.is_demo:
			category = 'Trials'
		elif self.category == 'tool':
			category = 'Applications'
		elif self.category != 'game':
			category = self.category.replace('_', ' ').title()
			
		self.metadata.categories = [category]

		platform = None
		if main_config.use_itch_io_as_platform:
			platform = 'itch.io'
		else:
			if self.game_type == 'flash':
				platform = 'Flash'
			elif self.game_type == 'java':
				platform = 'Java'
			elif self.game_type == 'html':
				platform = 'HTML'
			else:
				platform = '/'.join(['Mac' if plat == 'osx' else plat.title() for plat in self.platforms])
		self.metadata.specific_info['Game-Type'] = self.game_type
		self.metadata.platform = platform

	def try_and_find_exe(self, os_filter=None, no_arch_filter=False):
		#This is the fun part. There is no info in the receipt that actually tells us what to run, the way the itch.io app does it is use heuristics to figure that out. So if we don't have butler, we'd have to re-implement dash ourselves, which would suck and let's not
		#I still kinda want a fallback method that just grabs something ending with .x86 or .sh etc in the folder, though
		output = butler_configure(self.path, os_filter, no_arch_filter)
		if not output:
			#Bugger
			return []
		candidates = output['value']['candidates']
		if not candidates:
			return []
		#arch, size might also be useful
		#scriptInfo only applies if flavor == script (and just contains interpreter which shouldn't matter), windowsInfo only applies if flavour == windows
		return [(candidate['flavor'], os.path.join(output['value']['basePath'], candidate['path']), candidate.get('windowsInfo')) for candidate in candidates]

	def make_exe_launcher(self, flavour, exe_path, windows_info):
		metadata = copy.deepcopy(self.metadata)
		executable_name = os.path.basename(exe_path)
		metadata.specific_info['Executable-Name'] = executable_name
		if os.path.extsep in executable_name:
			metadata.extension = executable_name.rsplit(os.path.extsep, 1)[-1].lower()
		metadata.specific_info['Executable-Type'] = flavour
		#This shouldn't really happen, but sometimes the platform field in upload in the receipt is inaccurate
		#Pretend Mac doesn't exist
		if flavour in ('script', 'linux'):
			metadata.platform = 'Linux'
		elif flavour.startswith('windows'):
			metadata.platform = 'Windows'
		elif flavour == 'jar':
			metadata.platform = 'Java' #That will do
		elif flavour == 'html':
			metadata.platform = 'HTML'
		elif flavour == 'love':
			metadata.platform = 'LOVE'

		if os.path.isfile(exe_path):
			#Might be a folder if Mac, I guess
			add_metadata_for_raw_exe(exe_path, self.metadata)
			if 'icon' not in metadata.images:
				icon = look_for_icon_next_to_file(exe_path)
				if icon:
					metadata.images['Icon'] = icon

		params = get_launch_params(flavour, exe_path, windows_info)
		if not params:
			if main_config.debug and flavour not in ('app-macos', 'macos'):
				print(self.path, 'Not dealing with', flavour, exe_path, self.platforms, self.metadata.platform, 'yet')
			return
		if params[1]:
			metadata.emulator_name = params[1]

		desktop_launchers.make_launcher(params[0], self.name, metadata, 'itch.io', self.path)

	def make_launcher(self):
		os_filter = None
		if 'linux' in self.platforms:
			os_filter = 'linux'
		elif 'windows' in self.platforms:
			os_filter = 'windows'

		candidates = self.try_and_find_exe(os_filter)
		if not candidates:
			candidates = self.try_and_find_exe()

		if not candidates:
			if main_config.debug:
				print('No launch candidates found for', self.path)
			return

		candidate_basenames = [os.path.basename(path) for _, path, _ in candidates]

		for flavour, path, windows_info in candidates:
			if is_probably_unwanted_candidate(path, candidate_basenames):
				continue
			self.make_exe_launcher(flavour, path, windows_info)
	

def get_launch_params(flavour, exe_path, windows_info):
	if flavour in ('linux', 'script'):
		#ez pez
		return launcher.LaunchCommand(exe_path, []), None
	if flavour == 'html':
		#hmm I guess this will do
		return launcher.LaunchCommand('xdg-open', [exe_path]), None
	if flavour in ('windows', 'windows-script'):
		if windows_info and windows_info.get('dotNet', False):
			#Mono does not really count as an emulator but whateves (I mean neither does Wine by the name but for metadata purposes I will)
			return launcher.LaunchCommand('mono', [exe_path]), 'Mono'
		#gui might also be useful if it is false
		return launcher.get_wine_launch_params(exe_path, []), 'Wine'
	if flavour == 'jar':
		#Guess we can just assume it's installed who cares
		return launcher.LaunchCommand('java', ['-jar', exe_path]), None
	if flavour == 'love':
		#Guess we can also just assume this is installed who cares
		return launcher.LaunchCommand('love', [exe_path]), 'LOVE'

	return None
	
