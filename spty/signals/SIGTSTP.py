import atexit
import logging
import os
import signal
from typing import Optional


global_jobs = {}
logger = logging.getLogger("spty")


def build_tstp_handler(
    child_pid: int = 0, master_fd: int = 0, signal_fd: Optional[int] = None
):
    """build a SIGTSTP handler, with context about where is the child_pid, master_fd

    as default, the child_pid = 0 is meaning current pid, the master_fd = 0 is meaning current fd
    """

    def handler(signum, frame):
        atexit.register(killall_suspended_when_exited)
        if child_pid in global_jobs:
            raise ValueError("child have been suspended.")
        # hang up the process by sending SIGSTOP
        os.kill(child_pid, signal.SIGSTOP)
        # store the context for resuming
        global_jobs[child_pid] = (child_pid, master_fd, signal_fd)
        # send a signal to `streaming` there is a SIGTSTP
        if signal_fd:
            os.write(signal_fd, b"1")
        logger.warning("[%d] + %d suspended (signal)", len(global_jobs) + 1, child_pid)

    return handler


def resume_by_pid(pid):
    """resume a hung up process"""
    if pid not in global_jobs:
        raise ValueError("child have been wakeup.")
    os.kill(pid, signal.SIGCONT)
    child_pid, master_fd, signal_fd = global_jobs.pop(pid)
    # listen the SIGTSTP again
    signal.signal(signal.SIGTSTP, build_tstp_handler(child_pid, master_fd, signal_fd))
    return child_pid, master_fd, signal_fd


def killall_suspended_when_exited():
    """Avoid to product zombie process

    Note: It maybe works...? No test covered!
    """
    for pid in global_jobs:
        os.kill(pid, signal.SIGKILL)
