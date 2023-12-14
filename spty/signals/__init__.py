from typing import Optional, Dict
import signal
from . import SIGWINCH, SIGTSTP, SIGINT


__original_signals = {}


def reset_signals():
    for signum, handler in __original_signals.items():
        signal.signal(signum, handler)
    __original_signals.clear()


def initial_signals(grouped_context: Dict):
    """initial all signal should handle by an interactive tty"""
    # dispatch the signal to the default handler
    # for i in range(signal.NSIG):
    #     signal.signal(i, signal.SIG_DFL)

    # install extra handler, such as SIGWINCH...
    for signum, context in grouped_context.items():
        install_spty_handler(signum, context)


def install_spty_handler(signum, context: Optional[Dict] = None):
    """A shortcut for installing spty signal handler

    :param signum: the signum should be handled
    :param context: some extra context should the handler know
    """
    context = context or {}
    if signum == signal.SIGCHLD:
        raise NotImplementedError
    elif signum == signal.SIGPIPE:
        raise NotImplementedError
    elif signum == signal.SIGHUP:
        raise NotImplementedError
    elif signum == signal.SIGINT:
        __original_signals[signum] = signal.signal(signum, SIGINT.build_int_handler(**context))
    elif signum == signal.SIGWINCH:
        __original_signals[signum] = signal.signal(signum, SIGWINCH.build_winch_handler(**context))
    elif signum == signal.SIGTSTP:
        __original_signals[signum] = signal.signal(signum, SIGTSTP.build_tstp_handler(**context))
