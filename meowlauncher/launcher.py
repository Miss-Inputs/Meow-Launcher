import shlex
from abc import ABC, abstractmethod
from collections.abc import Iterable, MutableMapping, Sequence, Mapping
from typing import Any, Optional

from meowlauncher.config.main_config import main_config
from meowlauncher.game import Game
from meowlauncher.runner import Runner

#This is basically just here in case the path of a ROM changes between when we generate the LaunchCommand for the game and when we generate the actual launcher… it can't be just a sentinel object as sometimes you might want to replace something like "--arg=$<path>", unless I think of a better way to handle that
rom_path_argument = '$<path>'

class LaunchCommand():
	def __init__(self, exe_name: str, exe_args: Sequence[str], env_vars: Optional[MutableMapping[str, str]]=None, working_directory: Optional[str]=None):
		self._exe_name = exe_name
		self._exe_args = exe_args
		self._env_vars = {} if env_vars is None else env_vars
		self.working_directory = working_directory

	@property
	def exe_name(self) -> str:
		return self.exe_name

	@property
	def exe_args(self) -> Sequence[str]:
		return self.exe_args

	@property
	def env_vars(self) -> Mapping[str, str]:
		return self.env_vars

	def make_linux_command_string(self) -> str:
		exe_args_quoted = ' '.join(shlex.quote(arg) for arg in self.exe_args)
		exe_name_quoted = shlex.quote(self.exe_name)
		if self.env_vars:
			environment_vars = ' '.join([shlex.quote(k + '=' + v) for k, v in self.env_vars.items()])
			return f'env {environment_vars} {exe_name_quoted} {exe_args_quoted}'
		return exe_name_quoted + ' ' + exe_args_quoted

	def wrap(self, command: str) -> 'LaunchCommand':
		return LaunchCommand(command, [self.exe_name] + list(self._exe_args))

	def prepend_command(self, prepended_command: 'LaunchCommand') -> 'LaunchCommand':
		return MultiLaunchCommands([prepended_command], self, [])
		
	def append_command(self, appended_params: 'LaunchCommand') -> 'LaunchCommand':
		return MultiLaunchCommands([], self, [appended_params])

	def replace_path_argument(self, path: str) -> 'LaunchCommand':
		return LaunchCommand(self.exe_name, [arg.replace(rom_path_argument, path) for arg in self.exe_args], self._env_vars)

	def set_env_var(self, k: str, v: str) -> None:
		self._env_vars[k] = v

def get_wine_launch_params(exe_path: str, exe_args: Iterable[str], working_directory: Optional[str]=None) -> LaunchCommand:
	#TODO: Migrate to default_runners
	env_vars = None
	if main_config.wineprefix:
		env_vars = {'WINEPREFIX': main_config.wineprefix}

	args = ['start']
	if working_directory:
		args += ['/d', working_directory]
	args += ['/unix', exe_path]
	args += exe_args
	return LaunchCommand(main_config.wine_path, args, env_vars)

class MultiLaunchCommands(LaunchCommand):
	def __init__(self, pre_commands: Sequence[LaunchCommand], main_command: LaunchCommand, post_commands: Sequence[LaunchCommand], working_directory: str=None):
		self.pre_commands = list(pre_commands)
		self.main_command = main_command
		self.post_commands = list(post_commands)
		#self.working_directory = working_directory
		super().__init__('', '', {}, working_directory)

	@property
	def exe_name(self) -> str:
		#This probably doesn't make too much sense to be used… you probably want something like 'sh' and then exe_args has -c and the rest, if you ever really needed to access the exe_name of an existing LaunchCommand anyway
		#Or does it - the existing behaviour of MultiLaunchCommands.wrap is to just wrap the main command after all, maybe that is what we want to do too…
		#Mufufufufu
		return self.main_command.exe_name

	@property
	def exe_args(self) -> Sequence[str]:
		return self.main_command.exe_args

	@property
	def env_vars(self) -> Mapping[str, str]:
		return self.main_command.env_vars

	def get_whole_shell_command(self) -> LaunchCommand:
		#Purrhaps I should add an additional field for this object to optionally use ; instead of &&
		joined_commands = ' && '.join([command.make_linux_command_string() for command in self.pre_commands] + [self.main_command.make_linux_command_string()] + [command.make_linux_command_string() for command in self.post_commands])
		return LaunchCommand('sh', ('-c', joined_commands), dict(**self.env_vars), self.working_directory)

	def make_linux_command_string(self) -> str:
		return self.get_whole_shell_command().make_linux_command_string()

	def wrap(self, command: str) -> 'LaunchCommand':
		return MultiLaunchCommands(self.pre_commands, self.main_command.wrap(command), self.post_commands)

	def prepend_command(self, prepended_command: LaunchCommand) -> LaunchCommand:
		return MultiLaunchCommands([prepended_command] + self.pre_commands, self.main_command, self.post_commands)

	def append_command(self, appended_params: LaunchCommand) -> LaunchCommand:
		return MultiLaunchCommands(self.pre_commands, self.main_command, self.post_commands + [appended_params])

	def replace_path_argument(self, path: str) -> LaunchCommand:
		return MultiLaunchCommands(self.pre_commands, self.main_command.replace_path_argument(path), self.post_commands)
	
	def set_env_var(self, k: str, v: str) -> None:
		self.main_command.set_env_var(k, v)

class Launcher(ABC):
	def __init__(self, game: Game, runner: Runner) -> None:
		self.game = game
		self.runner = runner

	@property
	def name(self) -> str:
		return self.game.name

	@property
	@abstractmethod
	def game_type(self) -> str:
		pass
	
	@property
	@abstractmethod
	def game_id(self) -> str:
		pass

	@property
	def info_fields(self) -> dict[str, dict[str, Any]]:
		return self.game.metadata.to_launcher_fields()

	@abstractmethod
	def get_launch_command(self) -> LaunchCommand:
		pass
