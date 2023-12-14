"""Interrupt from keyboard (CTRL + C)."""
import logging
import os
import signal


logger = logging.getLogger("spty")


def build_int_handler(child_pid: int = 0):
    """build a SIGINT handler, with context about where is the child_pid

    as default, the child_pid = 0 is meaning current pid
    """

    def handler(signum, frame):
        interrupt_by_pid(pid=child_pid)
        logger.warning("process<%d> have interrupted (signal)", child_pid)

    return handler


def interrupt_by_pid(pid):
    try:
        os.kill(pid, signal.SIGINT)
    except ProcessLookupError:
        logger.warning("process<%d> have gone", pid)
