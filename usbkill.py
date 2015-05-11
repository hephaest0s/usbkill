#             _     _     _ _ _ 
#            | |   | |   (_) | |
#  _   _  ___| |__ | |  _ _| | |
# | | | |/___)  _ \| |_/ ) | | |
# | |_| |___ | |_) )  _ (| | | |
# |____/(___/|____/|_| \_)_|\_)_)
#
#
# Hephaestos <hephaestos@riseup.net> - 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import re
import subprocess
import platform
import os, sys, signal
from time import sleep
from datetime import datetime

# Get the current platform
CURRENT_PLATFORM = platform.system().upper()

# Darwin specific library
if CURRENT_PLATFORM.startswith("DARWIN"):
	import plistlib

# We compile this function beforehand for efficiency.
DEVICE_RE = [ re.compile(".+ID\s(?P<id>\w+:\w+)"), re.compile("0x([0-9a-z]{4})") ]

# Set the settings filename here
SETTINGS_FILE = '/etc/usbkill/settings.ini'

help_message = """
usbkill is a simple program with one goal: quickly shutdown the computer when a USB is inserted or removed.
Events are logged in /var/log/usbkill/kills.log
You can configure a whitelist of USB ids that are acceptable to insert and the remove.
The USB id can be found by running the command 'lsusb'.
Settings can be changed in /etc/usbkill/settings
In order to be able to shutdown the computer, this program needs to run as root.
"""

def log(settings, msg):
	log_file = settings['log_file']
	
	contents = '\n{0} {1}\nCurrent state:\n'.format(str(datetime.now()), msg)
	with open(log_file, 'a+') as log:
		log.write(contents)
	
	# Log current USB state
	if CURRENT_PLATFORM.startswith("DARWIN"):
		os.system("system_profiler SPUSBDataType >> " + log_file)
	else:
		os.system("lsusb >> " + log_file)

def shred(settings):
	shredder = settings['remove_file_command']
	
	# List logs and settings to be removed
	if settings['melt_usbkill']:
		settings['folders_to_remove'].append(os.path.dirname(settings['log_file']))
		settings['folders_to_remove'].append(os.path.dirname(SETTINGS_FILE))
		usbkill_folder = os.path.dirname(os.path.realpath(__file__))
		if usbkill_folder.upper().startswith('USB'):
			settings['folders_to_remove'].append(usbkill_folder)
		else:
			settings['files_to_remove'].append(os.path.realpath(__file__))
	
	# Remove files
	for _file in settings['files_to_remove']:
		os.system(shredder + _file)
	
	# Remove files in folders and the folders
	for folder in settings['folders_to_remove']:
		os.system("find " + folder + " -exec " + shredder + " {} \;")
		os.system("rm -rf " + folder) # this is in case the shredder doesn't handle folders (e.g. shred)
	
def kill_computer(settings):
	# Log what is happening:
	if not settings['melt_usbkill']: # No need to spend time on logging if logs will be removed
		log(settings, "Detected a USB change. Dumping the list of connected devices and killing the computer...")
	
	# Shred as specified in settings
	shred(settings)
	
	# Execute kill commands in order.
	for command in settings['kill_commands']:
		os.system(command)

	if settings['do_sync']:
		# Sync the filesystem to save recent changes
		os.system("sync")
	else:
		# If syncing is risky because it might take too long, then sleep for 5ms.
		# This will still allow for syncing in most cases.
		sleep(0.05)
	
	if settings['shut_down']: # Use argument --no-shut-down to prevent a shutdown.
		# Finally poweroff computer immediately
		if CURRENT_PLATFORM.startswith("DARWIN"):
			# OS X (Darwin) - Will halt ungracefully, without signaling apps
			os.system("killall Finder && killall loginwindow && halt -q")
		elif CURRENT_PLATFORM.endswith("BSD"):
			# BSD-based systems - Will shutdown
			os.system("shutdown -h now")
		else:
			# Linux-based systems - Will shutdown
			os.system("poweroff -f")
		
	# Exit the process to prevent executing twice (or more) all commands
	sys.exit(0)

def lsusb_darwin():
	# Use OS X system_profiler (native and 60% faster than lsusb port)
	df = subprocess.check_output("system_profiler SPUSBDataType -xml -detailLevel mini", shell=True)
	if sys.version_info[0] == 2:
		df = plistlib.readPlistFromString(df)
	elif sys.version_info[0] == 3:
		df = plistlib.loads(df)

	def check_inside(result, devices):
		"""
			I suspect this function can become more readable.
		"""
		# Do not take devices with Built-in_Device=Yes
		try:
			result["Built-in_Device"]
		except KeyError:
		
			# Check if vendor_id/product_id is available for this one
			try:
				assert "vendor_id" in result and "product_id" in result
				# Append to the list of devices
				devices.append(DEVICE_RE[1].findall(result["vendor_id"])[0] + ':' + DEVICE_RE[1].findall(result["product_id"])[0])
			except AssertionError: {}
		
		# Check if there is items inside
		try:
			# Looks like, do the while again
			for result_deep in result["_items"]:
				# Check what's inside the _items array
				check_inside(result_deep, devices)
					
		except KeyError: {}
		
	# Run the loop
	devices = []
	for result in df[0]["_items"]:
		check_inside(result, devices)
	return devices
	
def lsusb():
	# A Python version of the command 'lsusb' that returns a list of connected usbids
	if CURRENT_PLATFORM.startswith("DARWIN"):
		# Use OS X system_profiler (native and 60% faster than lsusb port)
		return lsusb_darwin()
	else:
		# Use lsusb on linux and bsd
		return DEVICE_RE[0].findall(subprocess.check_output("lsusb", shell=True).decode('utf-8').strip())

def program_present(program):
	if sys.version_info[0] == 3:
		# Python3
		from shutil import which 
		return which(program) != None
		
	else:
		"""
			Test if an executable exist in Python2
			-> http://stackoverflow.com/a/377028
		"""
		def is_exe(fpath):
			return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

		fpath, fname = os.path.split(program)
		if fpath:
			if is_exe(program):
				return True
		else:
			for path in os.environ["PATH"].split(os.pathsep):
				path = path.strip('"')
				exe_file = os.path.join(path, program)
				if is_exe(exe_file):
					return True
		return False
	
def load_settings(filename):
	# Libraries that are only needed in this function:
	from json import loads as jsonloads
	if sys.version_info[0] == 3:
		# Python3
		import configparser
		def get_setting(name, gtype=''):
			"""
				configparser: Compatibility layer for Python 2/3
				Function currently depends on a side effect, which is not necessary.
			"""
			section = config['config']
			if gtype == 'FLOAT':
				return section.getfloat(name)
			elif gtype == 'INT':
				return section.getint(name)
			elif gtype == 'BOOL':
				return section.getboolean(name)
			return section[name]
	else:
		#Python2
		import ConfigParser as configparser
		def get_setting(name, gtype=''):
			if gtype == 'FLOAT':
				return config.getfloat('config', name)
			elif gtype == 'INT':
				return config.getint('config', name)
			elif gtype == 'BOOL':
				return config.getboolean('config', name)
			return config.get('config', name)

	config = configparser.ConfigParser()

	# Read all lines of settings file
	config.read(filename)
		
	# Build settings
	settings = dict({
		'sleep_time' : get_setting('sleep', 'FLOAT'),
		'whitelist': jsonloads(get_setting('whitelist').strip()),
		'log_file': get_setting('log_file'),
		'melt_usbkill' : get_setting('melt_usbkill', 'BOOL'),
		'remove_file_command' : get_setting('remove_file_command') + " ",
		'files_to_remove' : jsonloads(get_setting('files_to_remove').strip()),
		'folders_to_remove' : jsonloads(get_setting('folders_to_remove').strip()),
		'do_sync' : get_setting('do_sync', 'BOOL'),
		'kill_commands': jsonloads(get_setting('kill_commands').strip())
	})

	return settings
	
def loop(settings):
	# Main loop that checks every 'sleep_time' seconds if computer should be killed.
	# Allows only whitelisted usb devices to connect!
	# Does not allow usb device that was present during program start to disconnect!
	start_devices = lsusb()
	acceptable_devices = set(start_devices + settings['whitelist'])
	
	# Write to logs that loop is starting:
	msg = "[INFO] Started patrolling the USB ports every " + str(settings['sleep_time']) + " seconds..."
	log(settings, msg)
	print(msg)

	# Main loop
	while True:
		# List the current usb devices
		current_devices = lsusb()
		
		# Check that no usbids are connected twice.
		# Two devices with same usbid implies a usbid copy attack
		if not len(current_devices) == len(set(current_devices)):
			settings['killer'](settings)
		
		# Check that all current devices are in the set of acceptable devices
		for device in current_devices:
			if device not in acceptable_devices:
				settings['killer'](settings)

		# Check that all start devices are still present in current devices
		for device in start_devices:
			if device not in current_devices:
				settings['killer'](settings)
				
		sleep(settings['sleep_time'])

def exit_handler(signum, frame):
	print("\n[INFO] Exiting because exit signal was received\n")
	log("[INFO] Exiting because exit signal was received")
	sys.exit(0)

def startup_checks():
	# Splash
	print("             _     _     _ _ _  \n" +
			"            | |   | |   (_) | | \n" +
			"  _   _  ___| |__ | |  _ _| | | \n" +
			" | | | |/___)  _ \| |_/ ) | | | \n" +
			" | |_| |___ | |_) )  _ (| | | | \n" +
			" |____/(___/|____/|_| \_)_|\_)_)\n")

	# Check arguments
	args = sys.argv[1:]
	
	# Check for help 
	if '-h' in args or '--help' in args:
		sys.exit(help_message)
	
	# Check if dev mode
	killer = kill_computer
	copy_settings = False
	if '--cs' in args:
		print("[NOTICE] Copying setting.ini to " + SETTINGS_FILE )
		args.remove('--cs')
		copy_settings = True
		
	shut_down = True
	if '--no-shut-down' in args:
		print("[NOTICE] Ready to execute all the (potentially destructive) commands, but NOT shut down the computer.")
		args.remove('--no-shut-down')
		shut_down = False
	
	# Check all other args
	if len(args) > 0:
		sys.exit("\n[ERROR] Argument not understood. Can only understand -h\n")

	# Check if program is run as root, else exit.
	# Root is needed to power off the computer.
	if not os.geteuid() == 0:
		sys.exit("\n[ERROR] This program needs to run as root.\n")

	# Warn the user if he does not have FileVault
	if CURRENT_PLATFORM.startswith("DARWIN"):
		try:
			# fdesetup return exit code 0 when true and 1 when false
			subprocess.check_output(["/usr/bin/fdesetup", "isactive"])
		except subprocess.CalledProcessError:
			print("[NOTICE] FileVault is disabled. Sensitive data SHOULD be encrypted.")

	if not os.path.isdir("/etc/usbkill/"):
		os.mkdir("/etc/usbkill/")

	# On first time use copy settings.ini to /etc/usebkill/settings.ini
	# If dev-mode, always copy and don't remove old settings
	if not os.path.isfile(SETTINGS_FILE) or copy_settings:
		sources_path = os.path.dirname(os.path.realpath(__file__)) + '/'
		if not os.path.isfile(sources_path + "settings.ini"):
			sys.exit("\n[ERROR] You have lost your settings file. Get a new copy of the settings.ini and place it in /etc/usbkill/ or in " + sources_path + "/\n")
		os.system("cp " + sources_path + "settings.ini " + SETTINGS_FILE)
		if not copy_settings:
			os.remove(sources_path + "settings.ini") 
		
	# Load settings
	settings = load_settings(SETTINGS_FILE)
	settings['killer'] = killer
	settings['shut_down'] = shut_down
	
	# Make sure shredder is available if it will be used
	if settings['melt_usbkill'] or len(settings['files_to_remove']) > 0 or len(settings['folders_to_remove']) > 0:
		program = settings['remove_file_command'].split(" ")[0]
		if not program_present(program):
			msg = "\n[ERROR] remove_file_command `" + program + "' specified in " + SETTINGS_FILE 
			msg += " is not installed on this system.\n"
			sys.exit(msg)
	
	# Make sure there is a logging folder
	log_folder = os.path.dirname(settings['log_file'])
	if not os.path.isdir(log_folder):
		os.mkdir(log_folder)
	
	return settings

if __name__=="__main__":
	# Register handlers for clean exit of program
	for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, ]:
		signal.signal(sig, exit_handler)
	
	# Run startup checks and load settings
	settings = startup_checks()

	# Start main loop
	loop(settings)
