import gzip
import lzma
import re
import subprocess
import zipfile
import zlib

#Use a number of different ways to crack open some archive formats and feast on the juicy file goo inside, depending on what the user has installed
#Use inbuilt Python libraries for zip and gz
#Prefer libarchive over py7zr, because it should theoretically be faster… would it be faster than Python's inbuilt zipfile as well? I'm not sure actually
#As a worst case scenario, try running 7z in a subprocess, which is slow and clunky but it will open anything and I suspect it is often installed

try:
	import py7zr
	have_py7zr = True
except ImportError:
	have_py7zr = False

try:
	import libarchive
	have_python_libarchive = True
except ImportError:
	have_python_libarchive = False

try:
	#I'm not aware of any other 7z command that avoids doing anything, so this will have to do, but it feels weird
	subprocess.check_call(['7z', '--help'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	have_7z_command = True
except (subprocess.CalledProcessError, OSError):
	have_7z_command = False

compressed_exts = ['7z', 'zip', 'gz', 'bz2', 'xz', 'tar', 'tgz', 'tbz', 'txz', 'rar']
#7z command line tool supports even more like exe, iso that would be weird and a bad idea to treat as an archive even though you can if you want, or lha which by all means is an archive but for emulation purposes we pretend is an archive; or just some weird old stuff that we would never see and I don't really feel like listing every single one of them
#rar might need that onen package and shouldn't exist but anyway
#We still do need to detect by extension, because otherwise .jar and .solarus and .dosz and other things deliberately acting as not a zip would be a zip
#For that reason this might not work as expected with ".tar.gz" instead of ".tgz" etc

#-- Stuff to read archive files that have no native Python support via 7z command line (we still need this for some obscure types if we do have py7zr)

class BadSubprocessedArchiveError(Exception):
	pass

class BadArchiveError(Exception):
	pass

sevenzip_path_regex = re.compile(r'^Path\s+=\s+(.+)$')
sevenzip_attr_regex = re.compile(r'^Attributes\s+=\s+(.+)$')
sevenzip_crc_regex = re.compile(r'^CRC\s+=\s+([\dA-Fa-f]+)$')
def subprocess_sevenzip_list(path: str) -> list[str]:
	proc = subprocess.run(['7z', 'l', '-slt', '--', path], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

	files = []
	found_file_line = False
	inner_filename = None
	is_directory = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_file_line = True
			continue
		sevenzip_path_match = sevenzip_path_regex.fullmatch(line)
		if found_file_line and sevenzip_path_match:
			if inner_filename is not None:
				files.append(inner_filename + '/' if is_directory else inner_filename)
			inner_filename = sevenzip_path_match.group(1)
			continue
		sevenzip_attr_match = sevenzip_attr_regex.fullmatch(line)
		if found_file_line and sevenzip_attr_match:
			is_directory = sevenzip_attr_match.group(1)[:2] == 'D_'
	if inner_filename:
		files.append(inner_filename + '/' if is_directory else inner_filename)

	return files
	
def subprocess_sevenzip_get(path: str, filename: str) -> bytes:
	with subprocess.Popen(['7z', 'e', '-so', '--', path, filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
		if proc.returncode != 0:
			raise BadSubprocessedArchiveError('{0}: {1}'.format(path, proc.returncode))
		if not proc.stdout:
			return b''
		return proc.stdout.read()

sevenzip_size_reg = re.compile(r'^Size\s+=\s+(\d+)$', flags=re.IGNORECASE)
def subprocess_sevenzip_getsize(path: str, filename: str) -> int:
	proc = subprocess.run(['7z', 'l', '-slt', '--', path, filename], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

	found_file_line = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_file_line = True
			continue
		if found_file_line:
			if fullmatch := sevenzip_size_reg.fullmatch(line):
				return int(fullmatch.group(1))

	#Resort to ugly slow method if we have to, but this is of course not optimal, and would only really happen with .gz I think
	return len(subprocess_sevenzip_get(path, filename))

def subprocess_sevenzip_crc(path: str, filename: str) -> int:
	proc = subprocess.run(['7z', 'l', '-slt', '--', path, filename], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

	this_filename = None
	filename_found = False
	for line in proc.stdout.splitlines():
		if filename == this_filename:
			filename_found = True
			crc_match = sevenzip_crc_regex.fullmatch(line)
			if crc_match:
				return int(crc_match[1], 16)

		sevenzip_path_match = sevenzip_path_regex.fullmatch(line)
		if sevenzip_path_match:
			this_filename = sevenzip_path_match[1]
			continue
	
	if filename_found:
		#return NotImplementedError(path, 'is an archive with no CRC')
		return zlib.crc32(sevenzip_get(path, filename)) & 0xffffffff
	raise FileNotFoundError(filename)
	
#--- Inbuilt Python stuff
def zip_list(path: str) -> list[str]:
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.namelist()

def zip_get(path: str, filename: str) -> bytes:
	with zipfile.ZipFile(path) as zip_file:
		with zip_file.open(filename, 'r') as file:
			return file.read()

def zip_getsize(path: str, filename: str) -> int:
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.getinfo(filename).file_size

def get_zip_crc32(path: str, filename: str) -> int:
	with zipfile.ZipFile(path) as zip_file:
		return zip_file.getinfo(filename).CRC & 0xffffffff

def gzip_get(path: str) -> bytes:
	with gzip.GzipFile(path) as gzip_file:
		return gzip_file.read()

def gzip_getsize(path: str) -> int:
	#Filename is ignored, there is only one in there
	with gzip.GzipFile(path, 'rb') as f:
		f.seek(0, 2)
		return f.tell()

#---- py7zr

def sevenzip_list(path: str) -> list[str]:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return sevenzip_file.getnames()

def sevenzip_get(path: str, filename: str) -> bytes:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return sevenzip_file.read([filename])[filename].read()

def sevenzip_getsize(path: str, filename: str) -> int:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return [i.uncompressed for i in sevenzip_file.list() if i.filename == filename][0]

def sevenzip_get_crc32(path: str, filename: str) -> int:
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return [i.crc32 for i in sevenzip_file.list() if i.filename == filename][0]

#----- python-libarchive

def libarchive_list(path) -> list[str]:
	with libarchive.Archive(path, 'r') as a:
		return list(a.iterpaths())

def libarchive_get(path: str, filename: str) -> bytes:
	with libarchive.Archive(path, 'r') as a:
		for item in a:
			if item.pathname == filename:
				return a.read(item.size)
	raise FileNotFoundError(filename)

def libarchive_getsize(path: str, filename: str) -> int:
	with libarchive.Archive(path, 'r') as a:
		for item in a:
			if item.pathname == filename:
				return item.size
	raise FileNotFoundError(filename)

#There is no crc32

#----- Entry points to this little archive helper
def compressed_list(path: str) -> list[str]:
	if zipfile.is_zipfile(path):
		try:
			return zip_list(path)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path) from badzipfile
	#We can't get gzip inner filename from the gzip module, so we will have to do it generically, which kinda sucks
	if have_py7zr and not have_python_libarchive and path.endswith('.7z'):
		try:
			return sevenzip_list(path)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path) from ex
	if have_python_libarchive:
		try:
			return libarchive_list(path)
		#pylint: disable=broad-except
		except Exception as ex:
			#Can't blame me for this one - python-libarchive only ever raises generic exceptions, so it's all I can catch
			raise BadArchiveError(path) from ex
	if have_7z_command:
		try:
			return subprocess_sevenzip_list(path)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(path) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')

def compressed_get(path: str, filename: str) -> bytes:
	if zipfile.is_zipfile(path):
		try:
			return zip_get(path, filename)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path + '/' + filename) from badzipfile
	if have_py7zr and not have_python_libarchive and path.endswith('.7z'):
		try:
			return sevenzip_get(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	if path.endswith('.gz'):
		try:
			return gzip_get(path)
		except gzip.BadGzipFile as badgzipfile:
			raise BadArchiveError(path + '/' + filename) from badgzipfile
	if have_python_libarchive:
		try:
			return libarchive_get(path, filename)
		#pylint: disable=broad-except
		except Exception as ex:
			#Can't blame me for this one - python-libarchive only ever raises generic exceptions, so it's all I can catch
			raise BadArchiveError(path + '/' + filename) from ex
	if have_7z_command:
		try:
			return subprocess_sevenzip_get(path, filename)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')
	
def compressed_getsize(path: str, filename: str) -> int:
	if zipfile.is_zipfile(path):
		try:
			return zip_getsize(path, filename)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path + '/' + filename) from badzipfile
	if have_py7zr and not have_python_libarchive and path.endswith('.7z'):
		try:
			return sevenzip_getsize(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	if path.endswith('.gz'):
		try:
			return gzip_getsize(path)
		except gzip.BadGzipFile as badgzipfile:
			raise BadArchiveError(path + '/' + filename) from badgzipfile
	if have_python_libarchive:
		try:
			return libarchive_getsize(path, filename)
		#pylint: disable=broad-except
		except Exception as ex:
			#Can't blame me for this one - python-libarchive only ever raises generic exceptions, so it's all I can catch
			raise BadArchiveError(path + '/' + filename) from ex
	if have_7z_command:
		try:
			return subprocess_sevenzip_getsize(path, filename)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')

def get_crc32_of_archive(path: str, filename: str) -> int:
	if zipfile.is_zipfile(path):
		try:
			return get_zip_crc32(path, filename)
		except zipfile.BadZipFile:
			pass
	if have_py7zr and path.endswith('.7z'):
		try:
			return sevenzip_get_crc32(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	if path.endswith('.gz'):
		#Do things the old fashioned way, since we can't use the gzip module to read any CRC that might be in the gzip header
		#This will raise an archive error if it's invalid so we don't need to raise another one
		return zlib.crc32(gzip_get(path)) & 0xffffffff
	if have_7z_command:
		try:
			return subprocess_sevenzip_crc(path, filename)
		except BadSubprocessedArchiveError as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	if have_python_libarchive:
		#Presumably this is slower for 7z archives etc than even subprocessing 7z to get it
		try:
			return zlib.crc32(libarchive_get(path, filename)) & 0xffffffff
		#pylint: disable=broad-except
		except Exception as ex:
			raise BadArchiveError(path + '/' + filename) from ex
	raise NotImplementedError('You have nothing to read', path, 'with, try installing 7z or py7zr or python-libarchive')
	
