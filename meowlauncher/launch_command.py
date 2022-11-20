import os
import shlex
from collections.abc import Collection, Mapping, MutableMapping, Sequence
from pathlib import Path, PurePath, PureWindowsPath

#This is basically just here in case the path of a ROM changes between when we generate the LaunchCommand for the game and when we generate the actual launcher… it can't be just a sentinel object as sometimes you might want to replace something like "--arg=$<path>", unless I think of a better way to handle that
rom_path_argument = '$<path>'

#I guess if one ever cared about Not Linux, you would need to split LaunchCommand into BaseLaunchCommand and subclasses, rename make_linux_command_string -> make_command_string, put in subclass

class LaunchCommand():
	def __init__(self, exe_name: PurePath, exe_args: Sequence[str], env_vars: MutableMapping[str, str] | None=None, working_directory: PurePath | None=None):
		self._exe_name = exe_name
		self._exe_args = exe_args
		self._env_vars = {} if env_vars is None else env_vars
		self.working_directory = working_directory

	@property
	def exe_name(self) -> PurePath:
		return self._exe_name

	@property
	def exe_args(self) -> Sequence[str]:
		return self._exe_args

	@property
	def env_vars(self) -> Mapping[str, str]:
		return self._env_vars

	def make_linux_command_string(self) -> str:
		exe_args_quoted = ' '.join(shlex.quote(arg) for arg in self.exe_args)
		exe_name_quoted = shlex.quote(str(self.exe_name))
		if self.env_vars:
			environment_vars = ' '.join(shlex.quote(k + '=' + v) for k, v in self.env_vars.items())
			return f'env {environment_vars} {exe_name_quoted} {exe_args_quoted}'
		return exe_name_quoted + ' ' + exe_args_quoted

	def wrap(self, command: PurePath) -> 'LaunchCommand':
		"""Uses command as the executable which then has this command as arguments"""
		new_args = [str(self.exe_name)]
		new_args.extend(self._exe_args)
		return LaunchCommand(command, new_args)

	def prepend_command(self, prepended_command: 'LaunchCommand') -> 'LaunchCommand':
		return MultiLaunchCommands((prepended_command, ), self, ())
		
	def append_command(self, appended_params: 'LaunchCommand') -> 'LaunchCommand':
		return MultiLaunchCommands((), self, (appended_params, ))

	def replace_path_argument(self, path: PurePath) -> 'LaunchCommand':
		path_arg = os.fspath(path)
		replaced_args = tuple(path_arg if arg == rom_path_argument else arg.replace(rom_path_argument, path_arg) for arg in self.exe_args)
		return LaunchCommand(self.exe_name, replaced_args, self._env_vars)

	def set_env_var(self, k: str, v: str) -> None:
		self._env_vars[k] = v

class MultiLaunchCommands(LaunchCommand):
	def __init__(self, pre_commands: Sequence[LaunchCommand], main_command: LaunchCommand, post_commands: Sequence[LaunchCommand], working_directory: PurePath | None=None):
		self.pre_commands = pre_commands
		self.main_command = main_command
		self.post_commands = post_commands
		#self.working_directory = working_directory
		super().__init__(main_command.exe_name, '', {}, working_directory)

	@property
	def exe_name(self) -> PurePath:
		"""
		This probably doesn't make too much sense to be used… you probably want something like 'sh' and then exe_args has -c and the rest, if you ever really needed to access the exe_name of an existing LaunchCommand anyway
		Or does it - the existing behaviour of MultiLaunchCommands.wrap is to just wrap the main command after all, maybe that is what we want to do too…
		Mufufufufu
		"""
		return self.main_command.exe_name

	@property
	def exe_args(self) -> Sequence[str]:
		return self.main_command.exe_args

	@property
	def env_vars(self) -> Mapping[str, str]:
		return self.main_command.env_vars

	@property
	def whole_shell_command(self) -> LaunchCommand:
		#Purrhaps I should add an additional field for this object to optionally use ; instead of &&
		inner_commands = tuple(command.make_linux_command_string() for command in self.pre_commands) + \
			(self.main_command.make_linux_command_string(), ) + \
			tuple(command.make_linux_command_string() for command in self.post_commands)
		joined_commands = ' && '.join(inner_commands)
		return LaunchCommand(Path('sh'), ('-c', joined_commands))

	def make_linux_command_string(self) -> str:
		return self.whole_shell_command.make_linux_command_string()

	def wrap(self, command: PurePath) -> 'LaunchCommand':
		return MultiLaunchCommands(self.pre_commands, self.main_command.wrap(command), self.post_commands)

	def prepend_command(self, prepended_command: LaunchCommand) -> LaunchCommand:
		new_precommands = [prepended_command]
		new_precommands.extend(self.pre_commands)
		return MultiLaunchCommands(new_precommands, self.main_command, self.post_commands)

	def append_command(self, appended_params: LaunchCommand) -> LaunchCommand:
		new_postcommands = list(self.post_commands)
		new_postcommands.append(appended_params)
		return MultiLaunchCommands(self.pre_commands, self.main_command, new_postcommands)

	def replace_path_argument(self, path: PurePath) -> LaunchCommand:
		return MultiLaunchCommands(self.pre_commands, self.main_command.replace_path_argument(path), self.post_commands)
	
	def set_env_var(self, k: str, v: str) -> None:
		self.main_command.set_env_var(k, v)

def launch_with_wine(wine_path: PurePath, wineprefix: PurePath | None, exe_path: PurePath, exe_args: Collection[str], working_directory: PureWindowsPath | None=None) -> LaunchCommand:
	env_vars = None
	if wineprefix:
		env_vars = {'WINEPREFIX': str(wineprefix)}

	args = ['start']
	if working_directory:
		args += ['/d', str(working_directory)]
	args += ('/unix', str(exe_path))
	args += exe_args
	return LaunchCommand(wine_path, args, env_vars)
