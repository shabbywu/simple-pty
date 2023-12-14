#!/usr/bin/env python
import sys
import time

from spty import spawn, fg


child_pid, exitcode = spawn(["top"])
while exitcode == -1:
    # the process is suspended by `Ctrl + Z`
    # resume if ten seconds after
    time.sleep(10)
    child_pid, exitcode = fg(child_pid)

# the process is exited, return the exitcode as it is
sys.exit(exitcode)
