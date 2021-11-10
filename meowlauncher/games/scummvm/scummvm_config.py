import configparser
import os
import subprocess

from meowlauncher.config.main_config import main_config


def _get_vm_config(path: str) -> configparser.ConfigParser:
	parser = configparser.ConfigParser()
	parser.optionxform = str #type: ignore
	parser.read(path)
	return parser

class ScummVMConfig():
	class __ScummVMConfig():
		def __init__(self) -> None:
			self.have_scummvm_config = os.path.isfile(main_config.scummvm_config_path)

			self.have_scummvm_exe = True
			try:
				self.scummvm_engines = self.get_vm_engines('scummvm')
			except FileNotFoundError:
				self.have_scummvm_exe = False

			if self.have_scummvm_config:
				self.scummvm_ini = _get_vm_config(main_config.scummvm_config_path)

		@staticmethod
		def get_vm_engines(exe_name) -> dict[str, str]:
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
		def have_scummvm(self):
			return self.have_scummvm_config and self.have_scummvm_exe
		
	__instance = None

	@staticmethod
	def getScummVMConfig():
		if ScummVMConfig.__instance is None:
			ScummVMConfig.__instance = ScummVMConfig.__ScummVMConfig()
		return ScummVMConfig.__instance

scummvm_config = ScummVMConfig.getScummVMConfig()
