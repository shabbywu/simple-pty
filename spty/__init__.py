"""An utils for easily spawning interactive pty, which listening some signal like `signal.SIGWINCH`"""
import os
import signal
from typing import Tuple, Callable, Optional

from os import close, waitpid, WIFEXITED, WEXITSTATUS, WIFSIGNALED, WTERMSIG
from pty import fork
from spty.signals import initial_signals
from spty.signals.SIGWINCH import set_winsize, get_size
from spty.signals.SIGTSTP import resume_by_pid
from spty.streaming import STDIN_FILENO, _read, redirect_stdin_to_fd
from spty.exceptions import SignalToStopTerminal

CHILD = 0
__ALL__ = ["spawn"]


def waitstatus_to_exitcode(status):
    """Convert a wait status to an exit code.

    backport from python3.9
    """
    if WIFEXITED(status):
        return WEXITSTATUS(status)
    elif WIFSIGNALED(status):
        return WTERMSIG(status)
    raise ValueError("unknown waitstatus")


def spawn(
    argv, master_read=_read, stdin_read=_read
) -> Tuple[int, int, Optional[Callable]]:
    """Create a spawned interactive process.

    :return: Tuple[child_pid, child_exit_code, optional callable to resume the child process]
        - only when child_exit_code is signal.SIGTSTP, the resume will be not None
    reference: https://github.com/python/cpython/blob/main/Lib/pty.py#L163
    """
    if type(argv) == type(""):
        argv = (argv,)

    pid, master_fd = fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)

    # here will only run by master
    # 1. install signal
    signal_fd, signal_slave_fd = os.openpty()
    initial_signals(
        {
            signal.SIGWINCH: {"master_fd": master_fd},
            signal.SIGTSTP: {
                "child_pid": pid,
                "master_fd": master_fd,
                "signal_fd": signal_fd,
            },
            signal.SIGINT: {"child_pid": pid},
        }
    )

    # 2. initial the window size
    set_winsize(master_fd, *get_size(STDIN_FILENO))
    # 3. redirect stdin to fd
    try:
        redirect_stdin_to_fd(master_fd, signal_fd, master_read, stdin_read)
    except SignalToStopTerminal:
        return (
            pid,
            -1,
            lambda: resume_child(pid, master_fd, signal_fd, master_read, stdin_read),
        )
    else:
        close(master_fd)
        child_pid, wait_status = waitpid(pid, 0)
        return child_pid, waitstatus_to_exitcode(wait_status), None


def resume_child(child_pid, master_fd, signal_fd, master_read, stdin_read):
    resume_by_pid(child_pid)
    # 3. redirect stdin to fd
    try:
        redirect_stdin_to_fd(master_fd, signal_fd, master_read, stdin_read)
    except SignalToStopTerminal:
        return (
            child_pid,
            signal.SIGTSTP,
            lambda: resume_child(
                child_pid, master_fd, signal_fd, master_read, stdin_read
            ),
        )
    else:
        close(master_fd)
        child_pid, wait_status = waitpid(child_pid, 0)
        return child_pid, waitstatus_to_exitcode(wait_status), None
