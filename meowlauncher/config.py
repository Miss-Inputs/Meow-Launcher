"""Instances of Settings are stored here"""

import itertools
import sys
from argparse import SUPPRESS, Action, ArgumentParser
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from typing import TYPE_CHECKING, NoReturn, Protocol, TypeVar, runtime_checkable

from meowlauncher.game_sources.settings import GOGConfig, ItchioConfig, SteamConfig
from meowlauncher.games.mame.mame_config import ArcadeMAMEConfig
from meowlauncher.games.roms.roms_config import ROMsConfig
from meowlauncher.global_runners import ScummVMConfig, WineConfig
from meowlauncher.settings.settings import MainConfig, Settings, sentinel
from meowlauncher.version import __version__

if TYPE_CHECKING:
	from argparse import _ArgumentGroup  # why did they make this private, anyway?

SettingsType_co = TypeVar('SettingsType_co', bound=Settings, covariant=True)

@runtime_checkable
class HasConfigClass(Protocol[SettingsType_co]):
	@classmethod
	def config_class(cls) -> type[SettingsType_co]:
		...


_settings_classes: Mapping[str | None, Collection[type[Settings]]] = {
	None: {MainConfig, WineConfig, ScummVMConfig},
	'game-sources': {
		ArcadeMAMEConfig,
		ROMsConfig,
		SteamConfig,
		GOGConfig,
		ItchioConfig,
	},
}
"""{help group, or None for settings that should show up in main --help: [settings in that help group]}"""


def _format_group_help(
	parser: ArgumentParser, groups: 'Collection[_ArgumentGroup]', *, add_root_section: bool = False
):
	if add_root_section:
		groups = [parser._positionals, parser._optionals, *groups]
	formatter = parser._get_formatter()
	actions = list(itertools.chain.from_iterable(group._group_actions for group in groups))
	formatter.add_usage(None, actions, parser._mutually_exclusive_groups)

	formatter.add_text(parser.description)

	for group in groups:
		formatter.start_section(group.title)
		formatter.add_text(group.description)
		formatter.add_arguments(group._group_actions)
		formatter.end_section()

	formatter.add_text(parser.epilog)
	return formatter.format_help()


def _group_help_action(groups: 'Collection[_ArgumentGroup]', *, add_root_section: bool = False):
	class GroupHelpAction(Action):
		def __init__(
			self,
			option_strings: Sequence[str],
			dest: str = SUPPRESS,
			help: str | None = None,  # noqa: A002 #ARGH you fucking dickheads
		) -> None:
			self.groups = groups
			super().__init__(option_strings, dest, nargs=0, help=help, default=SUPPRESS)

		def __call__(self, parser: ArgumentParser, *_args, **_kwargs) -> None:
			print(
				_format_group_help(parser, groups, add_root_section=add_root_section),
				file=sys.stderr,
			)
			parser.exit()

	return GroupHelpAction


class DefaultHelpAction(Action):
	def __init__(
		self,
		option_strings: Sequence[str],
		dest: str = SUPPRESS,
		help: str | None = None,  # noqa: A002
	) -> None:
		super().__init__(option_strings, dest, nargs=0, help=help, default=SUPPRESS)

	def __call__(self, parser: ArgumentParser, *_args, **_kwargs) -> NoReturn:
		parser.print_help()
		parser.exit()


def _setup_config() -> dict[type, Settings]:
	"""Initializes config with command line arguments, etc"""

	parser = ArgumentParser(
		add_help=False, prog=f'python -m {__package__}'
	)  # We will add our own help that doesn't just spew everything at the user all at once
	parser.add_argument('--version', action='version', version=__version__)

	option_to_config: dict[
		str, tuple[type[Settings], str]
	] = {}  # class name + key: (settings, key)
	help_groups: defaultdict[str | None, set[_ArgumentGroup]] = defaultdict(set)
	for help_group, classes in _settings_classes.items():
		for cls in classes:
			for k in cls.model_fields:
				option_to_config[f'{cls.__qualname__}.{k}'] = (cls, k)
			group = cls.add_argparser_group(parser)
			if not isinstance(group, ArgumentParser):
				help_groups[help_group].add(group)

	for help_group, groups in help_groups.items():
		if help_group is None:
			continue
		parser.add_argument(
			f'--help-{help_group}',
			action=_group_help_action(groups),
			help=f'Show help for {help_group} and exit',
		)
	parser.add_argument(
		'--help-all',
		action=DefaultHelpAction,
		help='Show this help and help for all groups and exit',
	)
	parser.add_argument(
		'--help',
		'-h',
		action=_group_help_action(help_groups[None], add_root_section=True),
		help='Show this help and exit',
	)

	settings: dict[type, Settings] = {}
	for k, v in vars(parser.parse_intermixed_args()).items():
		if v is sentinel:
			continue
		cls, option_name = option_to_config[k]
		if cls not in settings:
			# setdefault will still run the constructor if it's in there, so that's probably not too  helpful
			settings[cls] = cls()
		setattr(settings[cls], option_name, v)
	return settings


__current_config = _setup_config()


def current_config(cls: type[SettingsType_co] | HasConfigClass[SettingsType_co]) -> SettingsType_co:
	cls_ = cls.config_class() if isinstance(cls, HasConfigClass) else cls
	if cls_ not in __current_config:
		__current_config[cls_] = cls_()
	config = __current_config[cls_]
	assert isinstance(config, cls_)
	return config


main_config = current_config(MainConfig)
