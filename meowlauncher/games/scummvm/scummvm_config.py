import subprocess
from collections.abc import Mapping
from pathlib import Path

from meowlauncher.settings.settings import Settings
from meowlauncher.util.utils import NoNonsenseConfigParser


def _get_vm_config(path: Path) -> NoNonsenseConfigParser:
	parser = NoNonsenseConfigParser()
	parser.read(path)
	return parser

class ScummVMConfig(Settings):
	"""Config options relating to ScummVM as a GameSource"""
	@classmethod
	def section(cls) -> str:
		return 'ScummVM'

	@classmethod
	def prefix(cls) -> str | None:
		return 'scummvm'

	@configoption
	def use_original_platform(self) -> bool:
		'Set the platform in game info to the original platform instead of leaving blank'
		return False

	@configoption
	def scummvm_config_path(self) -> Path:
		"""Path to scummvm.ini, if not the default
		TODO: Should be on ScummVM Runner"""
		return Path('~/.config/scummvm/scummvm.ini').expanduser()

	@configoption
	def scummvm_exe_path(self) -> Path:
		"""Path to scummvm executable, if not the default
		TODO: Should be on ScummVM Runner"""
		return Path('scummvm')


class ConfiguredScummVM():
	"""Holder for ScummVM ini file and whether you have the path or not. TODO: This class sucks, get rid of it"""
	def __init__(self) -> None:
		self.config = ScummVMConfig()
		self.have_scummvm_config = self.config.scummvm_config_path.is_file()

		self.have_scummvm_exe = True
		try:
			self.scummvm_engines = self._get_vm_engines(self.config.scummvm_exe_path)
		except FileNotFoundError:
			self.have_scummvm_exe = False

		if self.have_scummvm_config:
			self.scummvm_ini = _get_vm_config(self.config.scummvm_config_path)

	@staticmethod
	def _get_vm_engines(exe_name: Path) -> Mapping[str, str]:
		try:
			proc = subprocess.run([exe_name, '--list-engines'], stdout=subprocess.PIPE, check=True, universal_newlines=True)
			lines = proc.stdout.splitlines()[2:] #Ignore header and ----

			engines = {}
			for line in lines:
				#Engine ID shouldn't have spaces, I think
				engine_id, name = line.rstrip().split(maxsplit=1)
				name = name.removesuffix(' [all games]')
				engines[engine_id] = name
			engines['agi'] = 'AGI' #Not this weird 'AGI v32qrrbvdsnuignedogsafgd' business
			return engines
		except subprocess.CalledProcessError:
			return {}

	@property
	def have_scummvm(self) -> bool:
		return self.have_scummvm_config and self.have_scummvm_exe
		
	__instance = None

	def __new__(cls) -> 'ConfiguredScummVM':
		if not ConfiguredScummVM.__instance:
			ConfiguredScummVM.__instance = object.__new__(cls)
		return ConfiguredScummVM.__instance

scummvm_config = ConfiguredScummVM()
