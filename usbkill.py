#!/usr/bin/env python3
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Contact: hephaestos@riseup.net - 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B

import re
import subprocess
import platform
import os, sys, signal
import configparser
from time import time, sleep
from datetime import datetime

# We compile this function beforehand for efficiency.
DEVICE_RE = re.compile(".+ID\s(?P<id>\w+:\w+)")

# Set the global settings path
SETTINGS_FILE = '/etc/usbkill/settings.ini'

help_message = """usbkill is a simple program with one goal: quickly shutdown the computer when a usb is inserted or removed.
It logs to /var/log/usbkill/
You can configure a whitelist of usb ids that are acceptable to insert and the remove.
The usb id can be found by running the command 'lsusb'.
Settings can be changed in local directory or /etc/usbkill/settings.ini

In order to be able to shutdown the computer, this program needs to run as root.
"""

def log(msg):
    logfile = "/var/log/usbkill/usbkill.log"

    with open(logfile, 'a') as f:
        # Empty line to separate log enties
        f.write('\n')

        # Log the message that needed to be logged:
        line = str(datetime.now()) + ' ' + msg
        f.write(line + '\n')
        print(line)

        # Log current usb state:
        f.write('Current state:\n')
    os.system("lsusb >> " + logfile)


def kill_computer():
    # Log what is happening:
    log("Detected USB change. Dumping lsusb and killing computer...")

    # Sync the filesystem so that the recent log entry does not get lost.
    os.system("sync")

    # Get the current platform
    CURRENT_PLATFORM = platform.system().upper()

    # Poweroff computer immediately
    if CURRENT_PLATFORM.startswith("DARWIN"):
        # OS X (Darwin) - Will reboot
        # Use Kernel Panic instead of shutdown command (30% faster and encryption keys are released)
        os.system("dtrace -w -n \"BEGIN{ panic();}\"")
    elif CURRENT_PLATFORM.endswith("BSD"):
        # BSD-based systems - Will shutdown
        os.system("shutdown -h now")
    else:
        # Linux-based systems - Will shutdown
        os.system("poweroff -f")

def lsusb():
    # A python version of the command 'lsusb' that returns a list of connected usbids
    df = subprocess.check_output("lsusb", shell=True).decode('utf-8')
    devices = []
    for line in df.split('\n'):
        if line:
            info = DEVICE_RE.match(line)
            if info:
                dinfo = info.groupdict()
                devices.append(dinfo['id'])
    return devices


def load_settings(filename):
    "Load settings from config file"
    # Load settings from local directory or global - if exists
    config = configparser.ConfigParser()
    config.read(['./settings.ini', SETTINGS_FILE])
    section = config['config']

    sleep_time = float(section['sleep'])
    devices = [d.strip() for d in section['whitelist'].split(' ')]
    return devices, sleep_time


def loop(whitelisted_devices, sleep_time):
    "Main loop"

    # Main loop that checks every 'sleep_time' seconds if computer should be killed.
    # Allows only whitelisted usb devices to connect!
    # Does not allow usb device that was present during program start to disconnect!
    start_devices = lsusb()
    acceptable_devices = set(start_devices + whitelisted_devices)

    # Write to logs that loop is starting:
    msg = "Started patrolling the USB ports every " + str(sleep_time) + " seconds..."
    log(msg)

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
            if device not in current_devices:
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
        print("Creating log directory")
        os.mkdir("/var/log/usbkill/")

    # Register handlers for clean exit of loop
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, exit_handler)

    # Load settings
    whitelisted_devices, sleep_time = load_settings(SETTINGS_FILE)

    log("Starting with whitelist: " + ",".join(whitelisted_devices) )

    # Start main loop
    loop(whitelisted_devices, sleep_time)
