import os
import tty
from select import select
from tty import setcbreak, tcgetattr, tcsetattr
from exceptions import SignalToStopTerminal

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2


def _writen(fd, data):
    """Write all the data to a descriptor.

    reference: https://github.com/python/cpython/blob/main/Lib/pty.py#L124
    """
    while data:
        n = os.write(fd, data)
        data = data[n:]


def _read(fd):
    """Default read function.

    reference: https://github.com/python/cpython/blob/main/Lib/pty.py#L130
    """
    return os.read(fd, 1024)


def _copy(master_fd, signal_fd, master_read=_read, stdin_read=_read):
    """Parent copy loop.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)

    # TODO: find a better way to transfer the signal
    Additional conditions
        signal_fd will be readable when a SIGTSTP is accepted.

    reference: https://github.com/python/cpython/blob/main/Lib/pty.py#L134
    """
    fds = [master_fd, STDIN_FILENO, signal_fd]
    while fds:
        rfds, _wfds, _xfds = select(fds, [], [])

        if signal_fd in rfds:
            os.read(signal_fd, 1)
            raise SignalToStopTerminal

        if master_fd in rfds:
            # Some OSes signal EOF by returning an empty byte string,
            # some throw OSErrors.
            try:
                data = master_read(master_fd)
            except OSError:
                data = b""
            if not data:  # Reached EOF.
                return  # Assume the child process has exited and is
                # unreachable, so we clean up.
            else:
                os.write(STDOUT_FILENO, data)

        if STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                fds.remove(STDIN_FILENO)
            else:
                _writen(master_fd, data)


def redirect_stdin_to_fd(master_fd, signal_fd, master_read=_read, stdin_read=_read):
    """redirect stdin to child processes"""
    # 1. set terminal mode to cbreak mode for shell simulation
    try:
        mode = tcgetattr(STDIN_FILENO)
        setcbreak(STDIN_FILENO)
        restore = True
    except tty.error:  # This is the same as termios.error
        restore = False

    # 2. copy stdin from master to slave, and copy stdout back. which is processing by select
    try:
        _copy(master_fd, signal_fd, master_read, stdin_read)
    finally:
        # 3. restore terminal mode back when needed
        if restore:
            tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)
