from pathlib import Path
import shlex
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from typing import Optional

#This is basically just here in case the path of a ROM changes between when we generate the LaunchCommand for the game and when we generate the actual launcher… it can't be just a sentinel object as sometimes you might want to replace something like "--arg=$<path>", unless I think of a better way to handle that
rom_path_argument = '$<path>'

#I guess if one ever cared about Not Linux, you would need to split LaunchCommand into BaseLaunchCommand and subclasses, rename make_linux_command_string -> make_command_string, put in subclass

class LaunchCommand():
	def __init__(self, exe_name: str, exe_args: Sequence[str], env_vars: Optional[MutableMapping[str, str]]=None, working_directory: Optional[str]=None):
		self._exe_name = exe_name
		self._exe_args = exe_args
		self._env_vars = {} if env_vars is None else env_vars
		self.working_directory = working_directory

	@property
	def exe_name(self) -> str:
		return self._exe_name

	@property
	def exe_args(self) -> Sequence[str]:
		return self._exe_args

	@property
	def env_vars(self) -> Mapping[str, str]:
		return self._env_vars

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

	def replace_path_argument(self, path: Path) -> 'LaunchCommand':
		path_arg = str(path.resolve())
		replaced_args = [path_arg if arg == rom_path_argument else arg.replace(rom_path_argument, path_arg) for arg in self.exe_args]
		return LaunchCommand(self.exe_name, replaced_args, self._env_vars)

	def set_env_var(self, k: str, v: str) -> None:
		self._env_vars[k] = v

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
		return LaunchCommand('sh', ('-c', joined_commands))

	def make_linux_command_string(self) -> str:
		return self.get_whole_shell_command().make_linux_command_string()

	def wrap(self, command: str) -> 'LaunchCommand':
		return MultiLaunchCommands(self.pre_commands, self.main_command.wrap(command), self.post_commands)

	def prepend_command(self, prepended_command: LaunchCommand) -> LaunchCommand:
		return MultiLaunchCommands([prepended_command] + self.pre_commands, self.main_command, self.post_commands)

	def append_command(self, appended_params: LaunchCommand) -> LaunchCommand:
		return MultiLaunchCommands(self.pre_commands, self.main_command, self.post_commands + [appended_params])

	def replace_path_argument(self, path: Path) -> LaunchCommand:
		return MultiLaunchCommands(self.pre_commands, self.main_command.replace_path_argument(path), self.post_commands)
	
	def set_env_var(self, k: str, v: str) -> None:
		self.main_command.set_env_var(k, v)

def launch_with_wine(wine_path: str, wineprefix: Optional[str], exe_path: str, exe_args: Iterable[str], working_directory: Optional[str]=None) -> LaunchCommand:
	env_vars = None
	if wineprefix:
		env_vars = {'WINEPREFIX': wineprefix}

	args = ['start']
	if working_directory:
		args += ['/d', working_directory]
	args += ['/unix', exe_path]
	args += exe_args
	return LaunchCommand(wine_path, args, env_vars)