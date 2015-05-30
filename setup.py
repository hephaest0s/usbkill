#!/usr/bin/env python

#             _     _     _ _ _
#            | |   | |   (_) | |
#  _   _  ___| |__ | |  _ _| | |
# | | | |/___)  _ \| |_/ ) | | |
# | |_| |___ | |_) )  _ (| | | |
# |____/(___/|____/|_| \_)_|\_)_)
#
#
# Hephaestos <hephaestos@riseup.net> - 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B
# <https://github.com/hephaest0s/usbkill>
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


from distutils.core import setup
from os import path

DIRNAME = path.dirname(path.realpath(__file__))

name = lambda x : path.join(DIRNAME, x)

setup(name='usbkill',
      version='1.0-rc.4',
      description='usbkill is an anti-forensic kill-switch that waits for a change on your USB ports and then immediately shuts down your computer.',
      author='Hephaestos',
      author_email='hephaestos@riseup.net',
      license='GPLv3',
      url='https://github.com/hephaest0s/usbkill',

      packages=['usbkill'],
      scripts=[name('install/usbkill')],
      data_files=[ ('/etc/', [ name('install/usbkill.ini') ]) ]
     )
