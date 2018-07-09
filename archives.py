import zipfile
import subprocess
import re

COMPRESSED_EXTS = ['7z', 'zip', 'gz', 'bz2', 'tar', 'tgz', 'tbz'] 
#7z supports more, but I don't expect to see them (in the case of things like .rar, I don't want them to be treated as valid archive types because they're evil proprietary formats and I want to eradicate them, and the case of things like .iso I'd rather they not be treated as archives)

class Bad7zException(Exception):
	pass
	
def zip_list(path):
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.namelist()

sevenzip_path_reg = re.compile(r'^Path\s+=\s+(.+)$', flags=re.IGNORECASE)
def sevenzip_list(path):
	#FIXME This is slow actually
	proc = subprocess.run(['7z', 'l', '-slt', path], stdout=subprocess.PIPE, universal_newlines=True)
	if proc.returncode != 0:
		exception_message = 'Something went wrong in sevenzip_list {0}: {1} {2}'.format(path, proc.returncode, proc.stdout)
		raise Bad7zException(exception_message)
		
	files = []
	found_file_line = False
	for line in proc.stdout.splitlines():
		#Ugghhh... this part is annoying.
		if line.startswith('------'):
			found_file_line = True
			continue
		if found_file_line and sevenzip_path_reg.fullmatch(line):
			files.append(sevenzip_path_reg.fullmatch(line).group(1))
			
	return files
	
def compressed_list(path):
	if path.lower().endswith('.zip'):
		try:
			return zip_list(path)
		except:
			pass
			
	return sevenzip_list(path)
	
def zip_getsize(path, filename):
	with zipfile.ZipFile(path, 'r') as zip_file:
		return zip_file.getinfo(filename).file_size

sevenzip_size_reg = re.compile(r'^Size\s+=\s+(\d+)$', flags=re.IGNORECASE)
def sevenzip_getsize(path, filename):
	proc = subprocess.run(['7z', 'l', '-slt', path, filename], stdout=subprocess.PIPE, universal_newlines=True)
	if proc.returncode != 0:
		raise Bad7zException('Something went wrong in sevenzip_getsize {0}: {1} {2}'.format(path, proc.returncode, proc.stdout))
		
	found_file_line = False
	for line in proc.stdout.splitlines():
		if line.startswith('------'):
			found_file_line = True
			continue
		if found_file_line and sevenzip_size_reg.fullmatch(line):
			return int(sevenzip_size_reg.fullmatch(line).group(1))
			
	return None
	
def compressed_getsize(path, filename):
	if path.lower().endswith('.zip'):
		return zip_getsize(path, filename)
	return sevenzip_getsize(path, filename)

def sevenzip_get(path, filename):
	process = subprocess.run(args=('7z', 'e', '-so', path, filename), stdout=subprocess.PIPE)
	return process.stdout
	
def zip_get(path, filename):
	with zipfile.ZipFile(path) as zip_file:
		with zip_file.open(filename, 'r') as file:
			return file.read()

def compressed_get(path, filename):
	if path.lower().endswith('.zip'):
		return zip_get(path, filename)
	return sevenzip_get(path, filename)
	
