#!/bin/bash
xscreensaver-command -time | grep non-blanked > /dev/null
exit $?
