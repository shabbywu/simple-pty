class SignalToStopTerminal(Exception):
    """Signal to Stop Terminal
    raise when the spawn process is running, but a SIGTSTP is received by the parent processes"""
