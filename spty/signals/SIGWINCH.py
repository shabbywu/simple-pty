"""Window resize signal."""
import fcntl
import os
import struct
import termios


STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2


def build_winch_handler(master_fd: int = 0):
    """build a SIGWINCH handler, with context about where is the master_fd

    as default, the master_fd = 0 is meaning current fd
    """

    def handler(signum, frame):
        set_winsize(master_fd, *get_size(STDIN_FILENO))

    return handler


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
    if not os.isatty(fd):
        return None

    winsize = struct.pack("HHHH", rows, cols, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
