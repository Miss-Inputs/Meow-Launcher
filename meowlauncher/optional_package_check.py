#!/usr/bin/env python3

import subprocess
from importlib.util import find_spec

from meowlauncher.game_sources.steam import have_steamfiles
from meowlauncher.games.common.pc_common_info import have_pefile
from meowlauncher.games.mac import have_machfs, have_macresources
from meowlauncher.games.scummvm.scummvm_config import scummvm_config
from meowlauncher.games.specific_behaviour.wii import have_pycrypto
from meowlauncher.util.archives import check_7z_command, have_py7zr, have_python_libarchive
from meowlauncher.util.utils import have_termcolor

try:
	from PIL import __version__ as pillow_version
except ImportError:
	have_pillow = False
	pillow_version = ''
else:
	have_pillow = True

have_pycdlib = find_spec('pycdlib') is not None

# TODO: Check for itch.io butler, once we refactor all that


def main() -> None:
	print('py7zr:', have_py7zr)
	print('python-libarchive:', have_python_libarchive)
	if have_pillow:
		print('Pillow installed, version', pillow_version)
	else:
		print('Pillow not installed or importable')
	print('pycdlib:', have_pycdlib)
	print('steamfiles:', have_steamfiles)
	print('machfs:', have_machfs)
	print('macresources:', have_macresources)
	print('pefile:', have_pefile)
	print('termcolor:', have_termcolor)
	print('pycrypto:', have_pycrypto)

	print('7z subprocess:', check_7z_command())
	try:
		print('MAME:', subprocess.check_output(['mame', '-version'], text=True))
	except FileNotFoundError:
		print('MAME not installed or not in path')
	except subprocess.CalledProcessError as ex:
		print('MAME produced an error', ex)
	# Hrm, these might not work from here, since they rely on config being loaded
	print('ScummVM executable:', scummvm_config.have_scummvm_exe)
	print('ScummVM is configured:', scummvm_config.have_scummvm_config)
	# TODO: Check hactool/nstool, all the other various databases and things in stuff.txt


if __name__ == '__main__':
	main()
