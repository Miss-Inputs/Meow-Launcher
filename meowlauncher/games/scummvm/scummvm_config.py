import subprocess
from collections.abc import Mapping
from pathlib import Path

from meowlauncher.config.main_config import old_main_config
from meowlauncher.util.utils import NoNonsenseConfigParser


def _get_vm_config(path: Path) -> NoNonsenseConfigParser:
	parser = NoNonsenseConfigParser()
	parser.read(path)
	return parser

class ScummVMConfig():
	#TODO: This should be a ConfiguredRunner
	class __ScummVMConfig():
		def __init__(self) -> None:
			self.have_scummvm_config = old_main_config.scummvm_config_path.is_file()

			self.have_scummvm_exe = True
			try:
				self.scummvm_engines = self._get_vm_engines(old_main_config.scummvm_exe_path)
			except FileNotFoundError:
				self.have_scummvm_exe = False

			if self.have_scummvm_config:
				self.scummvm_ini = _get_vm_config(old_main_config.scummvm_config_path)

		@staticmethod
		def _get_vm_engines(exe_name: str) -> Mapping[str, str]:
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

	@staticmethod
	def getScummVMConfig() -> __ScummVMConfig:
		if ScummVMConfig.__instance is None:
			ScummVMConfig.__instance = ScummVMConfig.__ScummVMConfig()
		return ScummVMConfig.__instance

scummvm_config = ScummVMConfig.getScummVMConfig()
