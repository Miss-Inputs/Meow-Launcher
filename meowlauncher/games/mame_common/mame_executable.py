import copy
import re
import subprocess
from collections.abc import Iterator
from typing import cast
from xml.etree import ElementTree

from meowlauncher.common_paths import cache_dir
from meowlauncher.config.main_config import main_config


class MachineNotFoundException(Exception):
	#This shouldn't be thrown unless I'm an idiot, but that may well happen
	pass

class MAMENotInstalledException(Exception):
	#This should always end up being caught, because I shouldn't assume the user has stuff installed
	pass

class MAMEExecutable():
	def __init__(self, path: str='mame'):
		self.executable = path
		self.version = self._get_version()
		self._xml_cache_path = cache_dir.joinpath(self.version)
		self._icons = None

	def _get_version(self) -> str:
		#Note that there is a -version option in (as of this time of writing, upcoming) MAME 0.211, but might as well just use this, because it works on older versions
		version_proc = subprocess.run([self.executable, '-help'], stdout=subprocess.PIPE, universal_newlines=True, check=True)
		#Let it raise FileNotFoundError deliberately if it is not found
		return version_proc.stdout.splitlines()[0]

	def _real_iter_mame_entire_xml(self) -> Iterator[tuple[str, ElementTree.Element]]:
		if main_config.use_xml_disk_cache:
			print('New MAME version found: ' + self.version + '; creating XML; this may take a while the first time it is run')
			self._xml_cache_path.mkdir(exist_ok=True, parents=True)

		with subprocess.Popen([self.executable, '-listxml'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
			#I'm doing what the documentation tells me to not do and effectively using proc.stdout.read
			if not proc.stdout:
				return
			try:
				for _, element in ElementTree.iterparse(proc.stdout):
					if element.tag == 'machine':
						my_copy = copy.copy(element)
						machine_name = element.attrib['name']

						if main_config.use_xml_disk_cache:
							self._xml_cache_path.joinpath(machine_name + '.xml').write_bytes(ElementTree.tostring(element))
						yield machine_name, my_copy
						element.clear()
			except ElementTree.ParseError as fuck:
				#Hmm, this doesn't show us where the error really is
				if main_config.debug:
					print('baaagh XML error in listxml', fuck)
		if main_config.use_xml_disk_cache:
			#Guard against the -listxml process being interrupted and screwing up everything, by only manually specifying it is done when we say it is done… wait does this work if it's an iterator? I guess it must if this exists
			self._xml_cache_path.joinpath('is_done').touch()

	def _cached_iter_mame_entire_xml(self) -> Iterator[tuple[str, ElementTree.Element]]:
		for cached_file in self._xml_cache_path.iterdir():
			if cached_file.suffix != '.xml':
				continue
			driver_name = cached_file.stem
			yield driver_name, ElementTree.parse(cached_file).getroot()
			
	def iter_mame_entire_xml(self) -> Iterator[tuple[str, ElementTree.Element]]:
		if not main_config.use_xml_disk_cache or self._xml_cache_path.joinpath('is_done').is_file():
			yield from self._cached_iter_mame_entire_xml()
		else:
			yield from self._real_iter_mame_entire_xml()
		
	def get_mame_xml(self, driver: str) -> ElementTree.Element:
		if main_config.use_xml_disk_cache:
			cache_file_path = self._xml_cache_path.joinpath(driver + '.xml')
			try:
				return ElementTree.parse(cache_file_path).getroot()
			except FileNotFoundError:
				pass

		try:
			proc = subprocess.run([self.executable, '-listxml', driver], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
		except subprocess.CalledProcessError as cpe:
			raise MachineNotFoundException(driver) from cpe

		xml = ElementTree.fromstring(proc.stdout).find('machine')
		if not xml:
			raise MachineNotFoundException(driver) #This shouldn't happen if -listxml didn't return success but eh
		return xml

	def listsource(self) -> Iterator[tuple[str, str]]:
		proc = subprocess.run([self.executable, '-listsource'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, check=True)
		#Return code should always be 0 so if it's not I dunno what to do about that and let's just panic instead
		for line in proc.stdout.splitlines():
			#Machine names and source files both shouldn't contain spaces, so this should be fine
			line_split = line.split(maxsplit=2)
			assert len(line_split) == 2, '-listsource output only one column???!! what'
			yield cast(tuple[str, str], tuple(line_split))
	
	def verifysoftlist(self, software_list_name: str) -> Iterator[str]:
		#Unfortunately it seems we cannot verify an individual software, which would probably take less time
		proc = subprocess.run([self.executable, '-verifysoftlist', software_list_name], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
		#Don't check return code - it'll return 2 if one software in the list is bad

		for line in proc.stdout.splitlines():
			#Bleh
			software_verify_matcher = re.compile(fr'romset {software_list_name}:(.+) is (?:good|best available)$')
			line_match = software_verify_matcher.match(line)
			if line_match:
				yield line_match[1]

	def verifyroms(self, basename: str) -> bool:
		try:
			#Note to self: Stop wasting time thinking you can make this faster
			subprocess.run([self.executable, '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
			return True
		except subprocess.CalledProcessError:
			return False

	#Other frontend commands: listfull, listclones, listbrothers, listcrc, listroms, listsamples, verifysamples, romident, listdevices, listslots, listmedia, listsoftware, verifysoftware, getsoftlist
