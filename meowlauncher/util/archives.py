import gzip
import io
import lzma
import os
import re
import subprocess
import zipfile
import zlib
from collections.abc import Iterator
from pathlib import Path

from meowlauncher.common_types import ByteAmount

__doc__ = """Use a number of different ways to open some archive formats and feast on the juicy file goo inside, depending on what the user has installed
Use inbuilt Python libraries for zip and gz
Would libarchive be faster than inbuilt gzip/zipfile? Not even sure, haven't been bothered benchmarking it
As a worst case scenario, try running 7z in a subprocess, which is slow and clunky but it will open… almost anything, in theory

7z command line tool supports even more like exe, iso that would be weird and a bad idea to treat as an archive even though you can if you want, or lha which by all means is an archive but for emulation purposes we pretend is an archive; or just some weird old stuff that we would never see and I don't really feel like listing every single one of them
rar might need that one package and shouldn't exist but anyway
We still do need to detect by extension, because otherwise .jar and .solarus and .dosz and other things deliberately acting as not a zip would be a zip
For that reason this might not work as expected with ".tar.gz" instead of ".tgz" etc (but who stores their ROMs like that?)
"""

try:
	import py7zr
	have_py7zr = True
except ModuleNotFoundError:
	have_py7zr = False

try:
	import libarchive
	have_python_libarchive = True
except ModuleNotFoundError:
	have_python_libarchive = False

try:
	#I'm not aware of any other 7z command that avoids doing anything, so this will have to do, but it feels weird
	subprocess.check_call(('7z', '--help'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	have_7z_command = True
except (subprocess.CalledProcessError, OSError):
	have_7z_command = False

#compressed_list is only used in CompressedROM, so we can be useful and get the size and CRC so we don't have to read the archive twice, if possible
FilenameWithMaybeSizeAndCRC = tuple[str, ByteAmount | None, int | None]

compressed_exts = {'7z', 'zip', 'gz', 'bz2', 'xz', 'tar', 'tgz', 'tbz', 'txz', 'rar'}

#-- Stuff to read archive files that have no native Python support via 7z command line (we still need this for some obscure types if we do have py7zr)

class BadSubprocessedArchiveError(Exception):
	"""7z subprocess failed"""

class BadArchiveError(Exception):
	pass

_sevenzip_path_regex = re.compile(r'^Path\s+=\s+(.+)$')
_sevenzip_attr_regex = re.compile(r'^Attributes\s+=\s+(.+)$')
_sevenzip_crc_regex = re.compile(r'^CRC\s+=\s+([\dA-Fa-f]+)$')
_sevenzip_size_reg = re.compile(r'^Size\s+=\s+(\d+)$')
#Looks like this:
#"scanning the drives, listing archive, blah blah"
#--
#Path = archive.7z
#blah blah blah
# 
#---------- (maybe not that exact amount of dashes, but more than the first part)
#Path = inner.file
#size attributes = blah
# 
#Path = another.one
#size attributes = blah
def subprocess_sevenzip_list(path: str) -> Iterator[FilenameWithMaybeSizeAndCRC]:
	proc = subprocess.run(['7z', 'l', '-slt', '--', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError(f'{path}: {proc.returncode} {proc.stdout} {proc.stderr}')

	found_inner_files = False
	inner_filename: str | None = None
	size = None
	crc = None
	is_directory = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_inner_files = True
			continue
		if not found_inner_files:
			continue

		sevenzip_path_match = _sevenzip_path_regex.fullmatch(line)
		if sevenzip_path_match:
			if inner_filename is not None:
				#Found next file, move along
				yield inner_filename + '/' if is_directory else inner_filename, size, crc
				inner_filename = None
			inner_filename = sevenzip_path_match[1]
			#This is the first one
			continue
		sevenzip_size_reg_match = _sevenzip_size_reg.fullmatch(line)
		if sevenzip_size_reg_match:
			size = ByteAmount(sevenzip_size_reg_match[1])
		sevenzip_attr_match = _sevenzip_attr_regex.fullmatch(line)
		if sevenzip_attr_match:
			is_directory = sevenzip_attr_match[1][:2] == 'D_'
		crc_match = _sevenzip_crc_regex.fullmatch(line)
		if crc_match:
			crc = int(crc_match[1], 16)

	if inner_filename:
		yield inner_filename + '/' if is_directory else inner_filename, size, crc
	
def subprocess_sevenzip_get(path: str, filename: str, offset: int=0, amount: int=-1) -> bytes:
	with subprocess.Popen(['7z', 'e', '-so', '--', path, filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
		stdout, _ = proc.communicate()
		if proc.returncode != 0:
			raise BadSubprocessedArchiveError(f'{path}: {proc.returncode}')
		if amount < 0:
			amount = len(stdout)
		if offset or amount:
			stdout = stdout[offset: offset+amount]
		return stdout

def subprocess_sevenzip_getsize(path: str, filename: str) -> ByteAmount:
	proc = subprocess.run(['7z', 'l', '-slt', '--', path, filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError(f'{path}: {proc.returncode} {proc.stdout} {proc.stderr}')

	found_file_line = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_file_line = True
			continue
		if found_file_line:
			if fullmatch := _sevenzip_size_reg.fullmatch(line):
				return ByteAmount(fullmatch.group(1))

	#Resort to ugly slow method if we have to, but this is of course not optimal, and would only really happen with .gz I think
	return ByteAmount(len(subprocess_sevenzip_get(path, filename)))

def subprocess_sevenzip_crc(path: str, filename: str) -> int:
	proc = subprocess.run(['7z', 'l', '-slt', '--', path, filename], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError(f'{path}: {proc.returncode} {proc.stdout}')

	this_filename = None
	filename_found = False
	for line in proc.stdout.splitlines():
		if filename == this_filename:
			filename_found = True
			crc_match = _sevenzip_crc_regex.fullmatch(line)
			if crc_match:
				return int(crc_match[1], 16)

		sevenzip_path_match = _sevenzip_path_regex.fullmatch(line)
		if sevenzip_path_match:
			this_filename = sevenzip_path_match[1]
			continue
	
	if filename_found:
		#return NotImplementedError(path, 'is an archive with no CRC')
		return zlib.crc32(subprocess_sevenzip_get(path, filename)) & 0xffffffff
	raise FileNotFoundError(filename)
	
#--- Inbuilt Python stuff
def zip_list(path: Path) -> Iterator[FilenameWithMaybeSizeAndCRC]:
	with zipfile.ZipFile(path, 'r') as zip_file:
		for info in zip_file.infolist():
			yield info.filename, ByteAmount(info.file_size), info.CRC & 0xffffffff

def zip_get(path: Path, filename: str, offset: int=0, amount: int=-1) -> bytes:
	with zipfile.ZipFile(path, 'r') as zip_file:
		with zip_file.open(filename, 'r') as file:
			if offset:
				file.seek(offset)
			return file.read(amount)

def zip_getsize(path: Path, filename: str) -> ByteAmount:
	with zipfile.ZipFile(path, 'r') as zip_file:
		return ByteAmount(zip_file.getinfo(filename).file_size)

def get_zip_crc32(path: Path, filename: str) -> int:
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.getinfo(filename).CRC & 0xffffffff

def gzip_get(path: Path, offset: int=0, amount: int=-1) -> bytes:
	with gzip.GzipFile(path, 'rb') as gzip_file:
		if offset:
			gzip_file.seek(offset)
		return gzip_file.read(amount)

def gzip_getsize(path: Path) -> ByteAmount:
	""""Gets size of a .gz file by opening it and seeking to the end, so it better be seekable
	Filename is ignored, there is only one in there"""
	with gzip.GzipFile(path, 'rb') as f:
		f.seek(0, io.SEEK_END)
		return ByteAmount(f.tell())

#---- py7zr

def sevenzip_list(path: Path) -> Iterator[FilenameWithMaybeSizeAndCRC]:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		for file in sevenzip_file.list():
			yield file.filename, file.uncompressed, file.crc32

def sevenzip_get(path: Path, filename: str, offset: int=0, amount: int=-1) -> bytes:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		file = sevenzip_file.read([filename])[filename]
		if offset:
			file.seek(offset)
		return file.read(amount)

def sevenzip_getsize(path: Path, filename: str) -> ByteAmount:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		for each in sevenzip_file.list():
			if each.filename == filename:
				return ByteAmount(each.uncompressed)
		raise FileNotFoundError(f'{filename} is not in {path}')

def sevenzip_get_crc32(path: Path, filename: str) -> int:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		for each in sevenzip_file.list():
			if each.filename == filename:
				return each.crc32
		
		raise FileNotFoundError(f'{filename} is not in {path}')

#----- python-libarchive

def libarchive_list(path: Path) -> Iterator[FilenameWithMaybeSizeAndCRC]:
	with path.open('rb') as f:
		with libarchive.Archive(f, 'r') as a:
			#Note: libarchive does _not_ close archives properly even when a context manager if the path was a string, according to the ResourceWarnings I get, so if we are going to handle that ourselves we might as well just use a Path (which libarchive does not support seemingly)
			for item in a:
				yield item.pathname, item.size, None

def libarchive_get(path: Path, filename: str, offset: int=0, amount: int=-1) -> bytes:
	with path.open('rb') as f:
		with libarchive.Archive(f, 'r') as a:
			for item in a:
				if item.pathname == filename:
					#Stream returned by readstream() doesn't support seek() by the looks of it
					data: bytes
					if amount != -1:
						with a.readstream(item.size) as streamy_boi:
							if not offset:
								return streamy_boi.read(amount)
							data = streamy_boi.read(offset + amount) #I guess we will just figure it out ourselves
					else:
						data = a.read(item.size)
					if amount == -1 and not offset:
						return data
					return data[offset: offset + amount]
	raise FileNotFoundError(filename)

def libarchive_getsize(path: Path, filename: str) -> ByteAmount:
	with path.open('rb') as f:
		with libarchive.Archive(f, 'r') as a:
			for item in a:
				if item.pathname == filename:
					return ByteAmount(item.size)
	raise FileNotFoundError(filename)

#There is no crc32

#----- Entry points to this little archive helper
def compressed_list(path: Path) -> Iterator[FilenameWithMaybeSizeAndCRC]:
	if zipfile.is_zipfile(path):
		try:
			yield from zip_list(path)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path) from badzipfile
	#We can't get gzip inner filename from the gzip module, so we will have to do it generically, which kinda sucks
	if have_py7zr and path.suffix == '.7z':
		try:
			yield from sevenzip_list(path)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path) from ex
	if have_python_libarchive:
		try:
			yield from libarchive_list(path)
		#pylint: disable=broad-except
		except Exception as ex:
			#Can't blame me for this one - python-libarchive only ever raises generic exceptions, so it's all I can catch
			raise BadArchiveError(path) from ex
	if have_7z_command:
		try:
			yield from subprocess_sevenzip_list(os.fspath(path))
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(path) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')

def compressed_get(path: Path, filename: str, offset: int=0, amount: int=-1) -> bytes:
	if zipfile.is_zipfile(path):
		try:
			return zip_get(path, filename, offset, amount)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from badzipfile
	if path.suffix == '.gz':
		try:
			return gzip_get(path, offset, amount)
		except gzip.BadGzipFile as badgzipfile:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from badgzipfile
	if have_py7zr and not have_python_libarchive and path.suffix == '.7z':
		#Sorry but libarchive seems to be faster for whatever reason
		try:
			return sevenzip_get(path, filename, offset, amount)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	if have_python_libarchive:
		try:
			return libarchive_get(path, filename, offset, amount)
		#pylint: disable=broad-except
		except Exception as ex:
			#Can't blame me for this one - python-libarchive only ever raises generic exceptions, so it's all I can catch
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	if have_7z_command:
		try:
			return subprocess_sevenzip_get(os.fspath(path), filename, offset, amount)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')
	
def compressed_getsize(path: Path, filename: str) -> ByteAmount:
	if zipfile.is_zipfile(path):
		try:
			return zip_getsize(path, filename)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from badzipfile
	if have_py7zr and path.suffix == '.7z':
		try:
			return sevenzip_getsize(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	if path.suffix == '.gz':
		try:
			return gzip_getsize(path)
		except gzip.BadGzipFile as badgzipfile:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from badgzipfile
	if have_python_libarchive:
		try:
			return libarchive_getsize(path, filename)
		#pylint: disable=broad-except
		except Exception as ex:
			#Can't blame me for this one - python-libarchive only ever raises generic exceptions, so it's all I can catch
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	if have_7z_command:
		try:
			return subprocess_sevenzip_getsize(os.fspath(path), filename)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')

def get_crc32_of_archive(path: Path, filename: str) -> int:
	if zipfile.is_zipfile(path):
		try:
			return get_zip_crc32(path, filename)
		except zipfile.BadZipFile:
			pass
	if have_py7zr and path.suffix == '.7z':
		try:
			return sevenzip_get_crc32(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	if path.suffix == '.gz':
		#Do things the old fashioned way, since we can't use the gzip module to read any CRC that might be in the gzip header
		#This will raise an archive error if it's invalid so we don't need to raise another one
		return zlib.crc32(gzip_get(path)) & 0xffffffff
	if have_7z_command:
		try:
			return subprocess_sevenzip_crc(os.fspath(path), filename)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	if have_python_libarchive:
		#Presumably this is slower for 7z archives etc than even subprocessing 7z to get it
		try:
			return zlib.crc32(libarchive_get(path, filename)) & 0xffffffff
		#pylint: disable=broad-except
		except Exception as ex:
			raise BadArchiveError(os.fspath(path) + '/' + filename) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')
	
