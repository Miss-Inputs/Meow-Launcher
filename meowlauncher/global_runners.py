import subprocess
from collections.abc import Mapping, Sequence
from functools import cached_property
from pathlib import Path, PurePath, PureWindowsPath
from typing import TYPE_CHECKING

from meowlauncher.game import Game
from meowlauncher.games.scummvm.scummvm_game import ScummVMGame
from meowlauncher.launch_command import LaunchCommand

from .runner import BaseRunnerConfig, Runner

if TYPE_CHECKING:
	pass


class WineConfig(BaseRunnerConfig):
	@classmethod
	def section(cls) -> str:
		return 'Wine'

	@classmethod
	def prefix(cls) -> str:
		return 'wine'

	wineprefix: Path | None = None
	"""WINEPREFIX env var"""


class Wine(Runner[Game]):
	def __init__(self) -> None:
		super().__init__()
		self.config: WineConfig

	@classmethod
	def exe_name(cls) -> str:
		return 'wine'

	@classmethod
	def config_class(cls) -> type[WineConfig]:
		return WineConfig

	def launch_windows_exe(
		self,
		exe_path: PurePath,
		exe_args: Sequence[str],
		working_directory: PureWindowsPath | None = None,
	) -> LaunchCommand:
		env_vars = None
		if self.config.wineprefix:
			env_vars = {'WINEPREFIX': str(self.config.wineprefix)}

		args = ['start']
		if working_directory:
			args += ['/d', str(working_directory)]
		args += ('/unix', str(exe_path))
		args += exe_args
		return LaunchCommand(self.exe_path, args, env_vars)


class ScummVMConfig(BaseRunnerConfig):
	"""Config options relating to ScummVM as a GameSource and a Runner"""

	@classmethod
	def section(cls) -> str:
		return 'ScummVM'

	@classmethod
	def prefix(cls) -> str | None:
		return 'scummvm'

	use_original_platform: bool = False
	'Set the platform in game info to the original platform instead of leaving blank'

	scummvm_config_path: Path = Path('~/.config/scummvm/scummvm.ini').expanduser()
	"""Path to scummvm.ini, if not the default"""


class ScummVM(Runner):
	def __init__(self) -> None:
		super().__init__()
		self.config: ScummVMConfig

	@classmethod
	def exe_name(cls) -> str:
		return 'scummvm'

	@classmethod
	def config_class(cls) -> type[ScummVMConfig]:
		return ScummVMConfig

	@cached_property
	def engine_list(self) -> Mapping[str, str]:
		"""Returns all engines compiled into this exe as {engine ID: display name}"""
		try:
			proc = subprocess.run(
				[self.exe_path, '--list-engines'], stdout=subprocess.PIPE, check=True, text=True
			)
			lines = proc.stdout.splitlines()[2:]  # Ignore header and ----

			engines = {}
			for line in lines:
				# Engine ID shouldn't have spaces, I think
				engine_id, name = line.rstrip().split(maxsplit=1)
				name = name.removesuffix(' [all games]')
				engines[engine_id] = name
			engines['agi'] = 'AGI'  # Not this weird 'AGI v32qrrbvdsnuignedogsafgd' business
		except subprocess.CalledProcessError:
			return {}
		else:
			return engines

	def get_game_command(self, game: 'Game') -> LaunchCommand:
		if not isinstance(game, ScummVMGame):
			raise TypeError(f'game should be ScummVMGame, not {type(game)}')
		args = ['-f']

		if (
			self.config.scummvm_config_path
			!= self.config.model_fields['scummvm_config_path'].get_default()
		):
			args.append(f'--config={self.config.scummvm_config_path}')
		args.append(game.game_id)
		return LaunchCommand(self.exe_path, args)
