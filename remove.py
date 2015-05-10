def which(program):
	"""
		Test if an executable exist in Python
		-> http://stackoverflow.com/a/377028
	"""
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			path = path.strip('"')
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file
	return None
	
# Remove logs and settings
if settings['remove_logs_and_settings']:

	# Continue only if a shredder is available
	if settings['remove_program']['path'] != None:
	
		# srm support
		if settings['remove_program']['path'].endswith("/srm"):

			def return_command(version):
				"""
					Return the right command based on the version of srm and the number of passes defined in settings
				"""
				if version[1] == '2': # Check if this is an 1.2.x version
					if version[2] <= '10':
						# srm 1.2.10 introduce new commands which have 3-pass (-doe -E)
						if settings['remove_passes'] == 7: # US Dod compliant 7-pass
							return '--force --recursive --dod'
						elif settings['remove_passes'] == 3: # US DoE compliant 3-pass
							return '--force --recursive --doe'
					elif version[2] == '9':
						# srm 1.2.9 moved --medium to -dod (-D)
						if settings['remove_passes'] == 7 or settings['remove_passes'] == 3: # US Dod compliant 7-pass
							return '--force --recursive --dod'
					elif version[2] <= '8':
						# srm 1.2.8 and above (used in OS X Yosemite) support only 7/1-pass
						if settings['remove_passes'] == 7 or settings['remove_passes'] == 3: # US Dod compliant 7-pass
							return '--force --recursive --medium'

				# Fallback to 1-pass erasing
				return  '--force --recursive --simple'
			
			# Return the right command for srm
			remove_command = return_command(settings['remove_program']['version'])

		# shred support
		elif settings['remove_program']['path'].endswith("/shred"):
		
			# Use find
			custom_start = 'find '
		
			if settings['remove_passes'] == 7: # US Dod compliant 7-pass
				remove_command = '-depth -type f -exec shred -f -n 7 -z -u {} \;'
			elif settings['remove_passes'] == 3: # US DoE compliant 3-pass
				remove_command = '-depth -type f -exec shred -f -n 3 -z -u {} \;'
			else: # Fallback to 0-pass erasing
				remove_command = '-depth -type f -exec shred -f -n 0 -z -u {} \;'

		# wipe support
		elif settings['remove_program']['path'].endswith("/wipe"):
			
			if settings['remove_passes'] == 7: # Probably not US Dod compliant 7-pass
				remove_command = '-frsc -Q 7'
			elif settings['remove_passes'] == 3: # Probably not US DoE compliant 3-pass
				remove_command = '-frsc -Q 3'
			else: # Fallback to 0-pass erasing
				remove_command = '-frsc -Q 0'

		# rm support
		elif settings['remove_program']['path'].endswith("/rm"):
		
			# Fallback to 0-pass erasing using rm
			remove_command = '-rf'
	
		# Set custom_start empty if not set
		try:
			custom_start
		except UnboundLocalError:
			custom_start = ''
			
		# Build the command
		remove_command = SHELL_SEPARATOR + custom_start + settings['remove_program']['path'] + ' ' + remove_command + ' '
		remove_command = remove_command.lstrip(SHELL_SEPARATOR) + os.path.dirname(settings['log_file']) + remove_command + os.path.dirname(SETTINGS_FILE) + remove_command + __file__
		
		# If the directory where the script is start with "usbkill" (e.g.: usbkill, usbkill-dev, usbkill-master...)
      if SOURCES_PATH.endswith('usbkill')
         remove_command = SOURCES_PATH
      
		# Execute the command
		os.system(remove_command)
		
		
		
				
		
	# Determine which secure tool should we use to remove files
	# If none is available, fallback to "rm"
	REMOVE_PROGRAMS = [
		which('srm'), # <http://srm.sourceforge.net/>
		which('shred'),# <http://linux.die.net/man/1/shred>
		which('wipe'), # <http://linux.die.net/man/1/wipe>
		which('rm') # <http://linux.die.net/man/1/rm>
	]
	if REMOVE_PROGRAMS[0] != None: # srm
		REMOVE_PROGRAM = dict({
				'path':	REMOVE_PROGRAMS[0],
				'version': re.findall("([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{1,2})+", subprocess.check_output(REMOVE_PROGRAMS[0] + ' --version', shell=True).decode('utf-8').strip())[0]
		})		
	elif REMOVE_PROGRAMS[1] != None: # shred
		REMOVE_PROGRAM = dict({
				'path':	REMOVE_PROGRAMS[1]
		})
	elif REMOVE_PROGRAMS[2] != None: # wipe
		REMOVE_PROGRAM = dict({
				'path':	REMOVE_PROGRAMS[2]
		})
	elif REMOVE_PROGRAMS[3] != None: # rm
		REMOVE_PROGRAM = dict({
				'path':	REMOVE_PROGRAMS[3]
		})
	else:
		REMOVE_PROGRAM = None
		print('[WARNING] Files removing has been disabled because no shredder has been found! Please install srm, shred, wipe or rm!')
