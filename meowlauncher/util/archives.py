"""Use a number of different ways to open some archive formats and feast on the juicy file goo inside, depending on what the user has installed
Use inbuilt Python libraries for zip and gz
Would libarchive be faster than inbuilt gzip/zipfile? Not even sure, haven't been bothered benchmarking it
As a worst case scenario, try running 7z in a subprocess, which is slow and clunky but it will open… almost anything, in theory
"""
import gzip
import io
import re
import subprocess
import zipfile
import zlib
from abc import ABC, abstractmethod
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Literal

from pydantic import ByteSize

if TYPE_CHECKING:
	from collections.abc import Iterator

try:
	import py7zr
	import py7zr.exceptions

	have_py7zr = True
except ModuleNotFoundError:
	have_py7zr = False

try:
	import libarchive

	have_python_libarchive = True
except ModuleNotFoundError:
	have_python_libarchive = False


def check_7z_command() -> tuple[Literal[True], str | None] | tuple[Literal[False], Exception]:
	"""Checks for the presence and working-ness of the 7z command. Returns (True, version) if successful, or (False, exception) if not"""
	try:
		proc = subprocess.run(('7z', '--help'), check=True, capture_output=True, text=True)
	except (subprocess.CalledProcessError, OSError) as ex:
		return False, ex
	else:
		return True, next((line for line in proc.stdout.splitlines() if line), None)


have_7z_command = check_7z_command()[0]

FilenameWithMaybeSizeAndCRC = tuple[PurePath, ByteSize | None, int | None]
"""compressed_list is only used in CompressedROM, so we can be useful and get the size and CRC so we don't have to read the archive twice, if possible"""

compressed_exts = {'7z', 'zip', 'gz', 'bz2', 'xz', 'tar', 'tgz', 'tbz', 'txz', 'rar'}
"""7z command line tool supports even more like exe, iso that would be weird and a bad idea to treat as an archive even though you can if you want, or lha which by all means is an archive but for emulation purposes we pretend is an archive; or just some weird old stuff that we would never see and I don't really feel like listing every single one of them
rar might need that one package and shouldn't exist but anyway
We still do need to detect by extension, because otherwise .jar and .solarus and .dosz and other things deliberately acting as not a zip would be a zip
For that reason this might not work as expected with ".tar.gz" instead of ".tgz" etc (but who stores their ROMs like that?)"""
# Would it be better to just have extensions to _not_ try reading as an archive?


class BadArchiveError(Exception):
	"""Something is wrong with this archive (or something went wrong extracting it, but we'll blame the archive)"""

	def __init__(self, archive_path: Path, *args) -> None:
		self.archive_path = archive_path
		super().__init__(*args)


class NoImplementationFoundError(NotImplementedError):
	def __init__(self, archive_path: PurePath) -> None:
		msg = f'You have nothing to read {archive_path} with, try installing 7z or py7zr or python-libarchive'
		super().__init__(msg)


class ArchiveImplementation(ABC):
	"""Common interface for all archive-reading things. These methods should only raise BadArchiveError or FileNotFoundError, so you should wrap any exceptions specific to modules so that callers of compressed_* don't have to know about them"""

	can_list = True
	"""Set this to False if this is something that doesn't have a meaningful concept of listing an archive (e.g. inbuilt gzip, which doesn't read the inner filename)"""

	@staticmethod
	@abstractmethod
	def should_attempt(archive_path: Path) -> bool:
		"""Return True if this path is something that this implementation should try and open and consider to be invalid if it can't (as opposed to just something it's not meant to do)"""

	@staticmethod
	@abstractmethod
	def is_available() -> bool:
		"""Returns if this is available or not"""

	@staticmethod
	@abstractmethod
	def list(archive_path: Path) -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
		...

	@staticmethod
	@abstractmethod
	def get(
		archive_path: Path, inner_filename: PurePath | str, offset: int = 0, amount: int = -1
	) -> bytes:
		...

	@classmethod
	def get_size(cls, archive_path: Path, inner_filename: PurePath | str) -> ByteSize:
		"""Get the uncompressed size of inner_filename, or leave it up to the default implementation here which just extracts the whole file and gets the length"""
		return ByteSize(len(cls.get(archive_path, inner_filename)))

	@classmethod
	def get_crc32(cls, archive_path: Path, inner_filename: PurePath | str) -> int:
		"""Get the CRC32 of inner_filename, or leave it up to the default implementation here which just extracts the whole file and computes the checksum"""
		return zlib.crc32(cls.get(archive_path, inner_filename))


class Subprocess7zHandler(ArchiveImplementation):
	"""Stuff to read archive files that have no native Python support via 7z command line (we still need this for some less used format if we do have py7zr)"""

	_sevenzip_path_regex = re.compile(r'^Path\s+=\s+(.+)$')

	@staticmethod
	def should_attempt(_: Path) -> bool:
		return True

	@staticmethod
	def is_available() -> bool:
		return have_7z_command

	@staticmethod
	def __parse_7z_list_output(output: str) -> 'Iterator[dict[str, str]]':
		found_inner_files = False
		current: dict[str, str] | None = None
		for line in output.splitlines():
			if not line:
				continue
			if line.startswith('------'):
				found_inner_files = True
				continue
			if not found_inner_files:
				continue
			match = Subprocess7zHandler._sevenzip_path_regex.fullmatch(line)
			if match:
				if current is not None:
					# This file has now ended, move onto the next
					yield current
				current = {'Path': match[1]}
			else:
				k, _, v = line.partition(' = ')
				if k and v and current:
					current[k] = v
		if current:
			# Last file
			yield current

	@staticmethod
	def list(path: 'Path') -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
		"""Runs 7z in a shell and parses the output to get the listing that way.
		Looks like this:
		"scanning the drives, listing archive, blah blah"
		--
		Path = archive.7z
		blah blah blah

		---------- (maybe not that exact amount of dashes, but more than the first part)
		Path = inner.file
		size attributes = blah

		Path = another.one
		size attributes = blah
		:raises BadArchiveError: If 7z process fails
		"""
		try:
			proc = subprocess.run(
				['7z', 'l', '-slt', '--', path], capture_output=True, text=True, check=True
			)
		except subprocess.CalledProcessError as ex:
			raise BadArchiveError(path) from ex

		for file in Subprocess7zHandler.__parse_7z_list_output(proc.stdout):
			# is_directory = 'Folder' in file or 'D_' in file.get('Attributes', '') #But do we need that?
			size = file.get('Size')
			crc = file.get('CRC')

			yield (
				Path(file['Path']),
				ByteSize(size) if size is not None else None,
				int(crc, base=16) if crc is not None else None,
			)

	@staticmethod
	def get(path: 'Path', filename: PurePath | str, offset: int = 0, amount: int = -1) -> bytes:
		try:
			proc = subprocess.run(
				['7z', 'e', '-so', '--', path, filename],
				stdout=subprocess.PIPE,
				stderr=subprocess.DEVNULL,
				check=True,
			)
		except subprocess.CalledProcessError as ex:
			raise BadArchiveError(path) from ex
		else:
			stdout = proc.stdout
			if amount < 0:
				amount = len(stdout)
			if offset or amount:
				stdout = stdout[offset : offset + amount]
			return stdout

	@classmethod
	def get_size(cls, path: 'Path', filename: PurePath | str) -> ByteSize:
		try:
			proc = subprocess.run(
				['7z', 'l', '-slt', '--', path, filename],
				capture_output=True,
				text=True,
				check=True,
			)
		except subprocess.CalledProcessError as ex:
			raise BadArchiveError(path) from ex
		else:
			file = next(Subprocess7zHandler.__parse_7z_list_output(proc.stdout))
			if not file:
				raise FileNotFoundError(filename)
			size = file.get('Size')
			if size is not None:
				return ByteSize(size)

			# Resort to ugly slow method if we have to, but this is of course not optimal, and would only really happen with .gz I think
			return super().get_size(path, filename)

	@classmethod
	def get_crc32(cls, path: 'Path', filename: PurePath | str) -> int:
		try:
			proc = subprocess.run(
				['7z', 'l', '-slt', '--', path, filename],
				capture_output=True,
				text=True,
				check=True,
			)
		except subprocess.CalledProcessError as ex:
			raise BadArchiveError(path) from ex
		else:
			file = next(Subprocess7zHandler.__parse_7z_list_output(proc.stdout))
			if not file:
				raise FileNotFoundError(filename)
			crc = file.get('CRC')
			if crc is not None:
				return int(crc, base=16)

			return super().get_crc32(path, filename)


# --- Inbuilt Python stuff


class ZipHandler(ArchiveImplementation):
	"""Inbuilt Python module, although only zip files"""

	@staticmethod
	def should_attempt(archive_path: Path) -> bool:
		return zipfile.is_zipfile(archive_path)

	@staticmethod
	def is_available() -> bool:
		return True

	@staticmethod
	def list(path: 'Path') -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
		try:
			with zipfile.ZipFile(path, 'r') as zip_file:
				for info in zip_file.infolist():
					yield PurePath(info.filename), ByteSize(info.file_size), info.CRC & 0xFFFFFFFF
		except zipfile.BadZipFile as ex:
			raise BadArchiveError(path) from ex

	@staticmethod
	def get(
		archive_path: Path, inner_filename: PurePath | str, offset: int = 0, amount: int = -1
	) -> bytes:
		try:
			with zipfile.ZipFile(archive_path, 'r') as zip_file, zip_file.open(
				str(inner_filename), 'r'
			) as file:
				if offset:
					file.seek(offset)
				return file.read(amount)
		except zipfile.BadZipFile as ex:
			raise BadArchiveError(archive_path, inner_filename) from ex

	@classmethod
	def get_size(cls, archive_path: Path, inner_filename: PurePath | str) -> ByteSize:
		try:
			with zipfile.ZipFile(archive_path, 'r') as zip_file:
				return ByteSize(zip_file.getinfo(str(inner_filename)).file_size)
		except zipfile.BadZipFile as ex:
			raise BadArchiveError(archive_path, inner_filename) from ex

	@staticmethod
	def get_crc32(archive_path: Path, inner_filename: PurePath | str) -> int:
		try:
			with zipfile.ZipFile(archive_path, 'r') as zip_file:
				return zip_file.getinfo(str(inner_filename)).CRC & 0xFFFFFFFF
		except zipfile.BadZipFile as ex:
			raise BadArchiveError(archive_path, inner_filename) from ex


class GzipHandler(ArchiveImplementation):
	"""Inbuilt Python gzip support"""

	can_list = False

	@staticmethod
	def should_attempt(archive_path: Path) -> bool:
		return archive_path.suffix.lower() == '.gz'

	@staticmethod
	def is_available() -> bool:
		return True

	@staticmethod
	def list(_: Path) -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
		"""No can do, the gzip module ignores the filename when reading"""
		raise NotImplementedError()

	@staticmethod
	def get(archive_path: Path, _: PurePath | str, offset: int = 0, amount: int = -1) -> bytes:
		"""inner_filename is ignored, as there is only one thing in there"""
		try:
			with gzip.GzipFile(archive_path, 'rb') as gzip_file:
				if offset:
					gzip_file.seek(offset)
				return gzip_file.read(amount)
		except gzip.BadGzipFile as ex:
			raise BadArchiveError(archive_path) from ex

	@classmethod
	def get_size(cls, archive_path: Path, _: PurePath | str) -> ByteSize:
		""" "Gets size of a .gz file by opening it and seeking to the end, so it better be seekable
		Filename is ignored, there is only one in there"""
		try:
			with gzip.GzipFile(archive_path, 'rb') as f:
				f.seek(0, io.SEEK_END)
				return ByteSize(f.tell())
		except gzip.BadGzipFile as ex:
			raise BadArchiveError(archive_path) from ex


class Py7zrHandler(ArchiveImplementation):
	@staticmethod
	def should_attempt(archive_path: Path) -> bool:
		return py7zr.is_7zfile(archive_path)

	@staticmethod
	def is_available() -> bool:
		return have_py7zr

	@staticmethod
	def list(archive_path: Path) -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
		try:
			with py7zr.SevenZipFile(archive_path, mode='r') as sevenzip_file:
				for file in sevenzip_file.list():
					yield PurePath(file.filename), file.uncompressed, file.crc32
		except py7zr.exceptions.ArchiveError as ex:
			raise BadArchiveError(archive_path) from ex

	@staticmethod
	def get(
		archive_path: Path, inner_filename: PurePath | str, offset: int = 0, amount: int = -1
	) -> bytes:
		if isinstance(inner_filename, PurePath):
			inner_filename = str(inner_filename)
		try:
			with py7zr.SevenZipFile(archive_path, mode='r') as sevenzip_file:
				file = sevenzip_file.read([inner_filename])[inner_filename]
				if offset:
					file.seek(offset)
				return file.read(amount)
		except py7zr.exceptions.ArchiveError as ex:
			raise BadArchiveError(archive_path, inner_filename) from ex

	@classmethod
	def get_size(cls, archive_path: Path, inner_filename: PurePath | str) -> ByteSize:
		if isinstance(inner_filename, PurePath):
			inner_filename = str(inner_filename)
		try:
			with py7zr.SevenZipFile(archive_path, mode='r') as sevenzip_file:
				for file in sevenzip_file.list():
					if file.filename == inner_filename:
						return ByteSize(file.uncompressed)
			raise FileNotFoundError(f'{inner_filename} is not in {archive_path}')
		except py7zr.exceptions.ArchiveError as ex:
			raise BadArchiveError(archive_path, inner_filename) from ex

	@classmethod
	def get_crc32(cls, archive_path: Path, inner_filename: PurePath | str) -> int:
		if isinstance(inner_filename, PurePath):
			inner_filename = str(inner_filename)
		try:
			with py7zr.SevenZipFile(archive_path, mode='r') as sevenzip_file:
				for file in sevenzip_file.list():
					if file.filename == inner_filename:
						return file.crc32
			raise FileNotFoundError(f'{inner_filename} is not in {archive_path}')
		except py7zr.exceptions.ArchiveError as ex:
			raise BadArchiveError(archive_path, inner_filename) from ex


class LibarchiveHandler(ArchiveImplementation):
	@staticmethod
	def should_attempt(archive_path: Path) -> bool:
		# libarchive.is_archive opens up the whole archive and tests formats so I dunno about that one, we'll just check the extension
		return bool(libarchive.is_archive_name(archive_path))

	@staticmethod
	def is_available() -> bool:
		return have_python_libarchive

	@staticmethod
	def list(archive_path: Path) -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
		try:
			with archive_path.open('rb') as f, libarchive.Archive(f, 'r') as a:
				for item in a:
					yield PurePath(item.pathname), item.size, None
		except Exception as ex:
			raise BadArchiveError(archive_path) from ex

	@staticmethod
	def get(
		archive_path: Path, inner_filename: PurePath | str, offset: int = 0, amount: int = -1
	) -> bytes:
		if isinstance(inner_filename, PurePath):
			inner_filename = str(inner_filename)
		try:
			with archive_path.open('rb') as f, libarchive.Archive(f, 'r') as a:
				for item in a:
					if item.pathname == inner_filename:
						data: bytes
						if amount != -1:
							# Stream returned by readstream() doesn't support seek() by the looks of it
							with a.readstream(item.size) as streamy_boi:
								if not offset:
									return streamy_boi.read(amount)
								data = streamy_boi.read(
									offset + amount
								)  # I guess we will just figure it out ourselves
						else:
							data = a.read(item.size)
						if amount == -1 and not offset:
							return data
						return data[offset : offset + amount]
			raise FileNotFoundError(f'{inner_filename} is not in {archive_path}')
		except Exception as ex:
			raise BadArchiveError(archive_path) from ex

	@classmethod
	def get_size(cls, archive_path: Path, inner_filename: PurePath | str) -> ByteSize:
		if isinstance(inner_filename, PurePath):
			inner_filename = str(inner_filename)
		try:
			with archive_path.open('rb') as f, libarchive.Archive(f, 'r') as a:
				for item in a:
					if item.pathname == inner_filename:
						return ByteSize(item.size)
			raise FileNotFoundError(f'{inner_filename} is not in {archive_path}')
		except Exception as ex:
			raise BadArchiveError(archive_path) from ex


# ----- Entry points to this little archive helper
handlers = (ZipHandler, GzipHandler, LibarchiveHandler, Py7zrHandler, Subprocess7zHandler)
"""All handlers, in order of preference. We want anything implemented in C/otherwise natively for speed, then normal standard libraries where possible, then pure Python libraries, and only use subprocess as a fallback"""


def compressed_list(path: 'Path') -> 'Iterator[FilenameWithMaybeSizeAndCRC]':
	for handler in handlers:
		if handler.can_list and handler.is_available() and handler.should_attempt(path):
			yield from handler.list(path)
			return

	raise NoImplementationFoundError(path)


def compressed_get(
	path: 'Path', filename: PurePath | str, offset: int = 0, amount: int = -1
) -> bytes:
	for handler in handlers:
		if handler.is_available() and handler.should_attempt(path):
			return handler.get(path, filename, offset, amount)

	raise NoImplementationFoundError(path / filename)


def compressed_getsize(path: 'Path', filename: PurePath | str) -> ByteSize:
	for handler in handlers:
		if handler.is_available() and handler.should_attempt(path):
			return handler.get_size(path, filename)

	raise NoImplementationFoundError(path / filename)


def get_crc32_of_archive(path: 'Path', filename: PurePath | str) -> int:
	# TODO: Deprioritize libarchive here, as having no functionality to read CRC32 out of the archive probably means that it would end up being slower than falling back to subprocess (maybe?)
	for handler in handlers:
		if handler.is_available() and handler.should_attempt(path):
			return handler.get_size(path, filename)

	raise NoImplementationFoundError(path / filename)
