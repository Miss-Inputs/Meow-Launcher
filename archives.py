import gzip
import lzma
import re
import subprocess
import zipfile
import zlib

try:
	import py7zr
	have_py7zr = True
except ImportError:
	have_py7zr = False

compressed_exts = ['7z', 'zip', 'gz', 'bz2', 'tar', 'tgz', 'tbz', 'rar', 'xz', 'txz']
#7z supports more, but we shouldn't treat them as archives (e.g. iso) as that might be weird

#-- Stuff to read archive files that have no native Python support via 7z command line (we still need this for some obscure types if we do have py7zr)

class BadSubprocessedArchiveError(Exception):
	pass

class BadArchiveError(Exception):
	pass

sevenzip_path_regex = re.compile(r'^Path\s+=\s+(.+)$')
sevenzip_attr_regex = re.compile(r'^Attributes\s+=\s+(.+)$')
sevenzip_crc_regex = re.compile(r'^CRC\s+=\s+([\dA-Fa-f]+)$')
def subprocess_sevenzip_list(path):
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
	files.append(inner_filename + '/' if is_directory else inner_filename)

	return files
	
def subprocess_sevenzip_crc(path, filename):
	#See also https://fastapi.metacpan.org/source/BJOERN/Compress-Deflate7-1.0/7zip/DOC/7zFormat.txt to do things the hard way
	proc = subprocess.run(['7z', 'l', '-slt', '--', path, filename], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

	this_filename = None
	for line in proc.stdout.splitlines():
		if filename == this_filename:
			crc_match = sevenzip_crc_regex.fullmatch(line)
			if crc_match:
				return int(crc_match[1], 16)

		sevenzip_path_match = sevenzip_path_regex.fullmatch(line)
		if sevenzip_path_match:
			this_filename = sevenzip_path_match[1]
			continue
	
	return FileNotFoundError(filename)
	
sevenzip_size_reg = re.compile(r'^Size\s+=\s+(\d+)$', flags=re.IGNORECASE)
def subprocess_sevenzip_getsize(path, filename):
	proc = subprocess.run(['7z', 'l', '-slt', '--', path, filename], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise BadSubprocessedArchiveError('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

	found_file_line = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_file_line = True
			continue
		if found_file_line and sevenzip_size_reg.fullmatch(line):
			return int(sevenzip_size_reg.fullmatch(line).group(1))

	#Resort to ugly slow method if we have to, but this is of course not optimal, and would only really happen with .gz I think
	return len(subprocess_sevenzip_get(path, filename))

def subprocess_sevenzip_get(path, filename):
	with subprocess.Popen(['7z', 'e', '-so', '--', path, filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
		if proc.returncode != 0:
			raise BadSubprocessedArchiveError('{0}: {1}'.format(path, proc.returncode))
		return proc.stdout.read()

#---
def zip_list(path):
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.namelist()

def zip_getsize(path, filename):
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.getinfo(filename).file_size

def get_zip_crc32(path, filename):
	with zipfile.ZipFile(path) as zip_file:
		return zip_file.getinfo(filename).CRC & 0xffffffff

def zip_get(path, filename):
	with zipfile.ZipFile(path) as zip_file:
		with zip_file.open(filename, 'r') as file:
			return file.read()

def gzip_getsize(path):
	#Filename is ignored, there is only one in there
	with gzip.GzipFile(path, 'rb') as f:
		f.seek(0, 2)
		return f.tell()

def gzip_get(path):
	with gzip.GzipFile(path) as gzip_file:
		return gzip_file.read()

def sevenzip_list(path):
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return sevenzip_file.getnames()

def sevenzip_get(path, filename):
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return sevenzip_file.read([filename])[filename].read()

def sevenzip_getsize(path, filename):
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return [i.uncompressed for i in sevenzip_file.list() if i.filename == filename][0]

def sevenzip_get_crc32(path, filename):
	with py7zr.SevenZipFile(path, mode='r') as sevenzip_file:
		return [i.crc32 for i in sevenzip_file.list() if i.filename == filename][0]

#----- Entry points to this little archive helper
def get_crc32_of_archive(path, filename):
	if zipfile.is_zipfile(path):
		try:
			return get_zip_crc32(path, filename)
		except zipfile.BadZipFile:
			pass
	if have_py7zr and path.endswith('.7z'):
		try:
			return sevenzip_get_crc32(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path) from ex
	if path.endswith('.gz'):
		#Do things the old fashioned way, since we can't use the gzip module to read any CRC that might be in the gzip header
		#This will raise an archive error if it's invalid so we don't need to raise another one
		return zlib.crc32(gzip_get(path)) & 0xffffffff
	try:
		return subprocess_sevenzip_crc(path, filename)
	except BadSubprocessedArchiveError as ex:
		raise BadArchiveError(path) from ex
	
def compressed_list(path):
	if zipfile.is_zipfile(path):
		try:
			return zip_list(path)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path) from badzipfile
	if have_py7zr and path.endswith('.7z'):
		try:
			return sevenzip_list(path)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path) from ex
	#We can't get gzip inner filename from the gzip module, so we will have to let 7z do it, which kinda sucks
	try:
		return subprocess_sevenzip_list(path)
	except BadSubprocessedArchiveError as ex:
		raise BadArchiveError(path) from ex
	

def compressed_getsize(path, filename):
	if zipfile.is_zipfile(path):
		try:
			return zip_getsize(path, filename)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path) from badzipfile
	if have_py7zr and path.endswith('.7z'):
		try:
			return sevenzip_getsize(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path) from ex
	if path.endswith('.gz'):
		try:
			return gzip_getsize(path)
		except gzip.BadGzipFile as badgzipfile:
			raise BadArchiveError(path) from badgzipfile
	try:
		return subprocess_sevenzip_getsize(path, filename)
	except BadSubprocessedArchiveError as ex:
		raise BadArchiveError(path) from ex

def compressed_get(path, filename):
	if zipfile.is_zipfile(path):
		try:
			return zip_get(path, filename)
		except zipfile.BadZipFile as badzipfile:
			raise BadArchiveError(path) from badzipfile
	if have_py7zr and path.endswith('.7z'):
		try:
			return sevenzip_get(path, filename)
		except (py7zr.Bad7zFile, lzma.LZMAError) as ex:
			raise BadArchiveError(path) from ex
	if path.endswith('.gz'):
		try:
			return gzip_get(path)
		except gzip.BadGzipFile as badgzipfile:
			raise BadArchiveError(path) from badgzipfile
	try:
		return subprocess_sevenzip_get(path, filename)
	except BadSubprocessedArchiveError as ex:
		raise BadArchiveError(path) from ex
