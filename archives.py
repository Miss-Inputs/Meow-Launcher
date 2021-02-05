import re
import subprocess
import zipfile

compressed_exts = ['7z', 'zip', 'gz', 'bz2', 'tar', 'tgz', 'tbz']
#7z supports more, but I don't expect to see them (in the case of things like .rar, I don't want them to be treated as
#valid archive types because they're evil proprietary formats and I want to eradicate them, and the case of things
#like .iso I'd rather they not be treated as archives)
class Bad7zException(Exception):
	pass

def zip_list(path):
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.namelist()

sevenzip_path_regex = re.compile(r'^Path\s+=\s+(.+)$')
sevenzip_attr_regex = re.compile(r'^Attributes\s+=\s+(.+)$')
sevenzip_crc_regex = re.compile(r'^CRC\s+=\s+([\dA-Fa-f]+)$')
def sevenzip_list(path):
	#This is rather slow…
	proc = subprocess.run(['7z', 'l', '-slt', path], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise Bad7zException('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

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
	
def sevenzip_crc(path, filename):
	#See also https://fastapi.metacpan.org/source/BJOERN/Compress-Deflate7-1.0/7zip/DOC/7zFormat.txt to do things the hard way
	proc = subprocess.run(['7z', 'l', '-slt', path], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise Bad7zException('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

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
	
def compressed_list(path):
	if zipfile.is_zipfile(path):
		try:
			return zip_list(path)
		except zipfile.BadZipFile:
			pass

	return sevenzip_list(path)

def zip_getsize(path, filename):
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.getinfo(filename).file_size

sevenzip_size_reg = re.compile(r'^Size\s+=\s+(\d+)$', flags=re.IGNORECASE)
def sevenzip_getsize(path, filename):
	proc = subprocess.run(['7z', 'l', '-slt', path, filename], stdout=subprocess.PIPE, universal_newlines=True, check=False)
	if proc.returncode != 0:
		raise Bad7zException('{0}: {1} {2}'.format(path, proc.returncode, proc.stdout))

	found_file_line = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_file_line = True
			continue
		if found_file_line and sevenzip_size_reg.fullmatch(line):
			return int(sevenzip_size_reg.fullmatch(line).group(1))

	return None

def compressed_getsize(path, filename):
	if zipfile.is_zipfile(path):
		try:
			return zip_getsize(path, filename)
		except zipfile.BadZipFile:
			pass
	return sevenzip_getsize(path, filename)

def sevenzip_get(path, filename):
	with subprocess.Popen(['7z', 'e', '-so', path, filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
		return proc.stdout.read()

def zip_get(path, filename):
	with zipfile.ZipFile(path) as zip_file:
		with zip_file.open(filename, 'r') as file:
			return file.read()

def compressed_get(path, filename):
	if zipfile.is_zipfile(path):
		try:
			return zip_get(path, filename)
		except zipfile.BadZipFile:
			pass
	return sevenzip_get(path, filename)

def get_zip_crc32(path, filename):
	with zipfile.ZipFile(path) as zip_file:
		return zip_file.getinfo(filename).CRC & 0xffffffff

def get_crc32_of_archive(path, filename):
	if zipfile.is_zipfile(path):
		try:
			return get_zip_crc32(path, filename)
		except zipfile.BadZipFile:
			pass
	return sevenzip_crc(path, filename)
	#return zlib.crc32(sevenzip_get(path, filename)) & 0xffffffff
