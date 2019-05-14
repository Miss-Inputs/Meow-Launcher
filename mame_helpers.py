import subprocess
import xml.etree.ElementTree as ElementTree
import re
import os
import copy

from metadata import CPU, ScreenInfo
from config import cache_dir
from common import junk_suffixes
from data.mame_manufacturers import manufacturer_overrides

def consistentify_manufacturer(manufacturer):
	if not manufacturer:
		return None
	manufacturer = junk_suffixes.sub('', manufacturer)
	return manufacturer_overrides.get(manufacturer, manufacturer)

mame_config_comment = re.compile(r'#.+$')
mame_config_line = re.compile(r'^(?P<key>\w+)\s+(?P<value>.+)$')
mame_config_values = re.compile(r'(".+"|[^;]+)') #Not sure if single quotes are okay too...
class MameConfigFile():
	def __init__(self, path):
		self.path = path
		self.settings = {}

		with open(path, 'rt') as f:
			for line in f.readlines():
				line = mame_config_comment.sub('', line)
				line = line.strip()

				if not line:
					continue

				match = mame_config_line.match(line)
				if match:
					key = match['key']
					value = mame_config_values.findall(match['value'])
					self.settings[key] = value

def get_mame_config():
	path = os.path.expanduser('~/.mame/mame.ini')
	if os.path.isfile(path):
		return MameConfigFile(path)
	raise FileNotFoundError(path)

def get_mame_ui_config():
	path = os.path.expanduser('~/.mame/ui.ini')
	if os.path.isfile(path):
		return MameConfigFile(path)
	raise FileNotFoundError(path)

class MachineNotFoundException(Exception):
	#This shouldn't be thrown unless I'm an idiot, but that may well happen
	pass

class MAMENotInstalledException(Exception):
	#This should always end up being caught, because I shouldn't assume the user has stuff installed
	pass

class MameState():
	class __MameState():
		def __init__(self):
			self.version = self.get_version()
			self.mame_xml_path = os.path.join(cache_dir, self.version) + '.xml' if self.have_mame else None
			self._have_checked_mame_xml = False
			self._icons = None

		@property
		def have_mame(self):
			return self.version is not None

		@staticmethod
		def get_version():
			try:
				version_proc = subprocess.run(['mame', '-help'], stdout=subprocess.PIPE, universal_newlines=True, check=True)
			except FileNotFoundError:
				#Should happen if and only if MAME isn't installed
				return None

			return version_proc.stdout.splitlines()[0]

		def _check_mame_xml_cache(self):
			if not self.have_mame:
				return
			if not os.path.isfile(self.mame_xml_path):
				print('New MAME version found: ' + self.version + '; creating XML; this may take a while (maybe like a minute or so)')
				os.makedirs(os.path.dirname(self.mame_xml_path), exist_ok=True)
				with open(self.mame_xml_path, 'wb') as f:
					subprocess.run(['mame', '-listxml'], stdout=f, stderr=subprocess.DEVNULL)
					#TODO check return code I guess (although in what ways would it fail?)
					#If this is interrupted you'll be left with a garbage XML file which then breaks when you parse it later... can we do something about that?
				print('Finished creating XML')

		def iter_mame_entire_xml(self):
			if not self.have_mame:
				raise MAMENotInstalledException()

			if not self._have_checked_mame_xml:
				#Should only check once
				self._check_mame_xml_cache()
				self._have_checked_mame_xml = True

			for _, element in ElementTree.iterparse(self.mame_xml_path):
				if element.tag == 'machine':
					yield element.attrib['name'], copy.copy(element)
					element.clear()

		def get_mame_xml(self, driver):
			if not self.have_mame:
				raise MAMENotInstalledException()

			try:
				proc = subprocess.run(['mame', '-listxml', driver], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
			except subprocess.CalledProcessError:
				raise MachineNotFoundException(driver)

			return ElementTree.fromstring(proc.stdout).find('machine')

		@property
		def icons(self):
			if self._icons is None:
				d = {}
				try:
					mame_ui_config = get_mame_ui_config()

					for icon_directory in mame_ui_config.settings.get('icons_directory', []):
						if os.path.isdir(icon_directory):
							for icon_file in os.listdir(icon_directory):
								name, ext = os.path.splitext(icon_file)
								if ext == '.ico': #Perhaps should have other formats?
									d[name] = os.path.join(icon_directory, icon_file)

					self._icons = d
				except FileNotFoundError:
					self._icons = d
			return self._icons

	__instance = None

	@staticmethod
	def getMameState():
		if MameState.__instance is None:
			MameState.__instance = MameState.__MameState()
		return MameState.__instance

mame_state = MameState.getMameState()

def have_mame():
	return mame_state.have_mame

def iter_mame_entire_xml():
	yield from mame_state.iter_mame_entire_xml()

def get_mame_xml(driver):
	return mame_state.get_mame_xml(driver)

def get_icons():
	return mame_state.icons

def find_cpus(machine_xml):
	#Type = "cpu" and not "audio", but this still refers to something that is there for sound output and not to do all the fun stuff
	audio_cpu_tags = ('audio_cpu', 'audiocpu', 'soundcpu', 'sound_cpu', 'genesis_snd_z80', 'pokey')

	cpu_xmls = [chip for chip in machine_xml.findall('chip') if chip.attrib.get('type') == 'cpu' and not chip.attrib.get('tag', '').split(':')[-1].startswith(audio_cpu_tags)]

	if not cpu_xmls:
		return []
	#Should 'master' + 'slave' count as 2 or should slave be skipped?

	cpus_with_cpu_tag = [cpu for cpu in cpu_xmls if cpu.attrib.get('tag') == 'cpu']
	if len(cpus_with_cpu_tag) == 1:
		#If there is more than one tagged 'cpu', things are more complicated and just continue as normal
		return cpus_with_cpu_tag

	#blah:blah is from a device which generally indicates it's a co-processor or controller for something else
	#:blah happens if we are looking at the device itself, which in that case yeah we probably do want the thing
	cpus_not_from_devices = [cpu for cpu in cpu_xmls if not (':' in cpu.attrib.get('tag') and not cpu.attrib.get('tag').startswith(':'))]
	if not cpus_not_from_devices:
		#The CPU might only be from a device in some cases
		return cpu_xmls

	return cpus_not_from_devices

def lookup_system_cpus(driver_name):
	machine = mame_state.get_mame_xml(driver_name)
	#Guess I'll pass the potential MAMENotInstalledException to caller

	cpu_list = []
	cpus = find_cpus(machine)
	if cpus:
		for cpu_xml in cpus:
			cpu = CPU()
			cpu.load_from_xml(cpu_xml)
			cpu_list.append(cpu)

	return cpu_list

def lookup_system_displays(driver_name):
	machine = mame_state.get_mame_xml(driver_name)

	displays = machine.findall('display')
	screen_info = ScreenInfo()
	screen_info.load_from_xml_list(displays)
	return screen_info
