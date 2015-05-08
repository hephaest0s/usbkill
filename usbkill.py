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
import plistlib
import os, sys, signal
from time import time, sleep

# We compile this function beforehand for efficiency.
DEVICE_RE = [ re.compile(".+ID\s(?P<id>\w+:\w+)"), re.compile("0x([0-9a-z]{4})") ]

# Set the settings filename here
SETTINGS_FILE = '/etc/usbkill/settings';
	
# Get the current platform
CURRENT_PLATFORM = platform.system().upper()

help_message = "usbkill is a simple program with one goal: quickly shutdown the computer when a usb is inserted or removed.\nIt logs to /var/log/usbkill/kills.log\nYou can configure a whitelist of USB ids that are acceptable to insert and the remove.\nThe USB id can be found by running the command 'lsusb'.\nSettings can be changed in /etc/usbkill/settings\n\nIn order to be able to shutdown the computer, this program needs to run as root.\n"

def log(msg):
	logfile = "/var/log/usbkill/usbkill.log"
	with open(logfile, 'a+') as log:
		contents = '\n{0} {1}\nCurrent state:'.format(str(time()), msg)
		log.write(contents)
	
	# Log current USB state
	if CURRENT_PLATFORM.startswith("DARWIN"):
		os.system("system_profiler SPUSBDataType >> " + logfile)
	else:
		os.system("lsusb >> " + logfile)
		
def kill_computer():
	# Log what is happening:
	log("Detected a USB change. Dumping the list of connected devices and killing the computer...")
	
	# Sync the filesystem so that the recent log entry does not get lost.
	os.system("sync")
	
	# Poweroff computer immediately
	if CURRENT_PLATFORM.startswith("DARWIN"):
		# OS X (Darwin) - Will halt ungracefully, without signaling apps
		os.system("killall loginwindow Finder && halt -q")
	elif CURRENT_PLATFORM.endswith("BSD"):
		# BSD-based systems - Will shutdown
		os.system("shutdown -h now")
	else:
		# Linux-based systems - Will shutdown
		os.system("poweroff -f")

def lsusb():
	
	# A Python version of the command 'lsusb' that returns a list of connected usbids
	if CURRENT_PLATFORM.startswith("DARWIN"):
	
		# Use OS X system_profiler (native and 60% faster than lsusb port)
		df = plistlib.loads(subprocess.check_output("system_profiler SPUSBDataType -xml -detailLevel mini", shell=True))
		devices = []
		
		def check_inside(result):
			
			# Do not take devices with Built-in_Device=Yes
			try:
				result["Built-in_Device"]
			except KeyError:
			
				# Check if vendor_id/product_id is available for this one
				try:
					result["vendor_id"]
					result["product_id"]
				
					# Append to the list of devices
					devices.append(DEVICE_RE[1].findall(result["vendor_id"])[0] + ':' + DEVICE_RE[1].findall(result["product_id"])[0])
					# debug: devices.append(result["vendor_id"] + ':' + result["product_id"])
				except KeyError: {}
			
			# Check if there is items inside
			try:				
				result["_items"]
				
				# Looks like, do the while again
				for result_deep in result["_items"]:
					# Check what's inside the _items array
					check_inside(result_deep)
						
			except KeyError: {}

		# Run the loop
		for result in df[0]["_items"]:
			check_inside(result)
		
		return devices
	else:
		# Use lsusb on linux and bsd
		return DEVICE_RE[0].findall(subprocess.check_output("lsusb", shell=True).decode('utf-8').strip())

def settings_template(filename):
	# Make sure there is the settings folder
	if not os.path.isdir("/etc/usbkill/"):
		os.mkdir("/etc/usbkill/")
		
	# Make sure there is a settings file
	if not os.path.isfile(filename):
		# Pre-populate the settings file if it does not exist yet
		with open(filename, 'w') as f:
			f.write("# whitelist command lists the usb ids that you want whitelisted\n")
			f.write("# find the correct usbid for your trusted usb using the command 'lsusb'\n")
			f.write("# usbid looks something line 0123:9abc\n")
			f.write("# Be warned! other parties can copy your trusted usbid to another usb device!\n")
			f.write("# use whitelist command and single space separation as follows:\n")
			f.write("# whitelist usbid1 usbid2 etc\n")
			f.write("whitelist \n\n")
			f.write("# allow for a certain amount of sleep time between checks, e.g. 0.5 seconds:\n")
			f.write("sleep 0.5\n")

def load_settings(filename):
	# read all lines of settings file
	with open(filename, 'r') as f:
		lines = f.readlines()
	
	# Find the only two supported settings
	devices = None
	sleep_time = None
	for line in lines:
		if line[:10] == "whitelist ":
			devices = line.replace("\n","").replace("  "," ").split(" ")[1:]
		if line[:6] == "sleep ":
			sleep_time = float(line.replace("\n","").replace("  "," ").split(" ").pop())

	assert not None in [devices, sleep_time], "Please set the 'sleep' and 'whitelist' parameters in '/etc/usbkill/settings' !"
	assert sleep_time > 0.0, "Please allow for positive non-zero 'sleep' delay between USB checks!"
	return devices, sleep_time
	
def loop(whitelisted_devices, sleep_time):
	# Main loop that checks every 'sleep_time' seconds if computer should be killed.
	# Allows only whitelisted usb devices to connect!
	# Does not allow usb device that was present during program start to disconnect!
	start_devices = lsusb()
	acceptable_devices = set(start_devices + whitelisted_devices)
	
	# Write to logs that loop is starting:
	msg = "Started patrolling the USB ports every " + str(sleep_time) + " seconds..."
	log(msg)
	print(msg)
	
	# Main loop
	while True:
		# List the current usb devices
		current_devices = lsusb()
		
		# Check that all current devices are in the set of acceptable devices
		for device in current_devices:
			if device not in acceptable_devices:
				kill_computer()

		# Check that all start devices are still present in current devices
		for device in start_devices:
			# Practically prevent multiple devices with the same Vendor/Product ID to be connected
			if current_devices.count(device) != 1:
				kill_computer()
				
		sleep(sleep_time)

def exit_handler(signum, frame):
	print("\nExiting because exit signal was received\n")
	log("Exiting because exit signal was received")
	sys.exit(0)

if __name__=="__main__":
	# Check arguments
	args = sys.argv[1:]
	if '-h' in args or '--help' in args:
		sys.exit(help_message)
	elif len(args) > 0:
		sys.exit("\nArgument not understood. Can only understand -h\n")
		
	# Check if program is run as root, else exit.
	# Root is needed to power off the computer.
	if not os.geteuid() == 0:
		sys.exit("\nThis program needs to run as root.\n")
	
	# Make sure there is a logging folder
	if not os.path.isdir("/var/log/usbkill/"):
		os.mkdir("/var/log/usbkill/")
	
	# Make sure settings file is available
	settings_template(SETTINGS_FILE)

	# Register handlers for clean exit of loop
	for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, ]:
		signal.signal(sig, exit_handler)
		
	# Load settings
	whitelisted_devices, sleep_time = load_settings(SETTINGS_FILE)
	
	# Start main loop
	loop(whitelisted_devices, sleep_time)
	
