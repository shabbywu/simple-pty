"""An utils for easily spawning interactive pty, which listening some signal like `signal.SIGWINCH`"""
import fcntl
import os
import signal
import struct
import termios
import tty

from os import close, waitpid
from pty import fork
from select import select
from tty import setraw, tcgetattr, tcsetattr


__all__ = ["spawn"]


STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

CHILD = 0


def get_size(fd):
    """
    Return a tuple (rows, cols, xpix, ypix) representing the size of the TTY `fd`.
    The provided file descriptor should be the stdout stream of the TTY.
    If the TTY size cannot be determined, returns None.
    """
    if not os.isatty(fd):
        return None
    try:
        dims = struct.unpack("hhhh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "hhhhhhhh"))
    except:
        try:
            dims = (os.environ["LINES"], os.environ["COLUMNS"], 0, 0)
        except:
            return None
    return dims


def set_winsize(fd, rows, cols, xpix=0, ypix=0):
    """set the termios.TIOCSWINSZ to the fd."""
    winsize = struct.pack("HHHH", rows, cols, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


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


def _copy(master_fd, master_read=_read, stdin_read=_read):
    """Parent copy loop.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)

    reference: https://github.com/python/cpython/blob/main/Lib/pty.py#L134
    """
    fds = [master_fd, STDIN_FILENO]
    while fds:
        rfds, _wfds, _xfds = select(fds, [], [])

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


def spawn(argv, master_read=_read, stdin_read=_read):
    """Create a spawned process.

    reference: https://github.com/python/cpython/blob/main/Lib/pty.py#L163
    """
    if type(argv) == type(""):
        argv = (argv,)

    pid, master_fd = fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)

    try:
        mode = tcgetattr(STDIN_FILENO)
        setraw(STDIN_FILENO)
        restore = True
    except tty.error:  # This is the same as termios.error
        restore = False

    def handle_winsize(signum, frame):
        if signum != signal.SIGWINCH:
            return
        set_winsize(master_fd, *get_size(STDIN_FILENO))

    signal.signal(signal.SIGWINCH, handle_winsize)
    set_winsize(master_fd, *get_size(STDIN_FILENO))

    try:
        _copy(master_fd, master_read, stdin_read)
    finally:
        if restore:
            tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    close(master_fd)
    return waitpid(pid, 0)[1]
