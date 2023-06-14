"""Logging for Flow360."""
import os
from typing import Union
from datetime import datetime
from rich.console import Console
from typing_extensions import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogValue = Union[int, LogLevel]

# Logging levels compatible with logging module
_level_value = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

_level_name = {v: k for k, v in _level_value.items()}
_level_print_style = {
    "DEBUG": "DEBUG",
    "INFO": "[cyan]INFO[/cyan]",
    "WARNING": "[yellow]WARNING[/yellow]",
    "ERROR": "[bold red]ERROR[/bold red]",
    "CRITICAL": "[bold underline red]CRITICAL[/bold underline red]",
}

DEFAULT_LEVEL = "INFO"


def _get_level_int(level: LogValue) -> int:
    """Get the integer corresponding to the level string."""
    if isinstance(level, int):
        return level

    level_upper = level.upper()
    if level_upper != level:
        log.warning(
            f"'{level}' provided as a logging level. "
            "In the future, only upper-case logging levels may be specified. "
            f"This value will be converted to upper case '{level_upper}'."
        )
    if level_upper not in _level_value:
        # We don't want to import ConfigError to avoid a circular dependency
        raise ValueError(
            f"logging level {level_upper} not supported, must be "
            "'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'"
        )
    return _level_value[level_upper]


# pylint: disable=too-few-public-methods
class LogHandler:
    """Handle log messages depending on log level"""

    def __init__(
        self,
        console: Console,
        level: LogValue,
        fname: str = None,
        back_up_count: int = 10,
        maxBytes: int = 10000,
        write_to_file: bool = True,
    ):
        self.level = _get_level_int(level)
        self.console = console
        self.backupCount = back_up_count
        self.maxBytes = maxBytes
        self.fname = fname
        self.write_to_file = write_to_file

    def handle(self, level, level_name, message):
        """Output log messages depending on log level"""
        try:
            if self.fname is not None and self.shouldRollover(message):
                self.doRollover()
        except Exception as error:
            self.console.log(
                _level_print_style.get(_level_value["ERROR"], "unknown"),
                "Fail to Rollover" + error,
                sep=": ",
            )

        if level >= self.level and self.write_to_file:
            self.console.log(_level_print_style.get(level_name, "unknown"), message, sep=": ")

    def rotate(self, source, dest):
        if os.path.exists(source):
            os.rename(source, dest)

    def rotation_filename(self, name, counter):
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d-%H")
        return name + formatted_time + "." + str(counter)

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(self.fname, i)
                dfn = self.rotation_filename(self.fname, i + 1)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.fname, 1)
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.fname, dfn)

    def shouldRollover(self, message):
        """
        Determine if rollover should occur.

        Basically, see if the supplied message would cause the file to exceed
        the size limit we have.
        """
        # See bpo-45401: Never rollover anything other than regular files
        if not os.path.exists(self.fname) or not os.path.isfile(self.fname):
            return False
        if self.maxBytes > 0:  # are we rolling over?
            msg = "%s\n" % message
            if os.path.getsize(self.fname) + len(msg) >= self.maxBytes:
                return True
        return False


class Logger:
    """Custom logger to avoid the complexities of the logging module"""

    def __init__(self):
        self.handlers = {}

    def _log(self, level: int, level_name: str, message: str) -> None:
        """Distribute log messages to all handlers"""
        for handler in self.handlers.values():
            handler.handle(level, level_name, message)

    def log(self, level: LogValue, message: str, *args) -> None:
        """Log (message) % (args) with given level"""
        if isinstance(level, str):
            level_name = level
            level = _get_level_int(level)
        else:
            level_name = _level_name.get(level, "unknown")
        self._log(level, level_name, message % args)

    def debug(self, message: str, *args) -> None:
        """Log (message) % (args) at debug level"""
        self._log(_level_value["DEBUG"], "DEBUG", message % args)

    def info(self, message: str, *args) -> None:
        """Log (message) % (args) at info level"""
        self._log(_level_value["INFO"], "INFO", message % args)

    def warning(self, message: str, *args) -> None:
        """Log (message) % (args) at warning level"""
        message = message % args
        message = f"[white]{message}[/white]"
        self._log(_level_value["WARNING"], "WARNING", message)

    def error(self, message: str, *args) -> None:
        """Log (message) % (args) at error level"""
        message = message % args
        message = f"[white]{message}[/white]"
        self._log(_level_value["ERROR"], "ERROR", message)

    def critical(self, message: str, *args) -> None:
        """Log (message) % (args) at critical level"""
        message = message % args
        message = f"[white]{message}[/white]"
        self._log(_level_value["CRITICAL"], "CRITICAL", message)


# Initialize FLow360's logger
log = Logger()


def get_file_path(fname):
    return os.path.dirname(__file__) + "/flow360/logs/" + fname


def set_logging_level(level: LogValue = DEFAULT_LEVEL) -> None:
    """Set tidy3d console logging level priority.
    Parameters
    ----------
    level : str
        The lowest priority level of logging messages to display. One of ``{'DEBUG', 'INFO',
        'WARNING', 'ERROR', 'CRITICAL'}`` (listed in increasing priority).
    """
    if "console" in log.handlers:
        log.handlers["console"].level = _get_level_int(level)


def set_logging_console(stderr: bool = False) -> None:
    """Set stdout or stderr as console output
    Parameters
    ----------
    stderr : bool
        If False, logs are directed to stdout, otherwise to stderr.
    """
    if "console" in log.handlers:
        previous_level = log.handlers["console"].level
    else:
        previous_level = DEFAULT_LEVEL
    log.handlers["console"] = LogHandler(Console(stderr=stderr, log_path=False), previous_level)


def set_logging_file(
    fname: str,
    filemode: str = "w",
    level: LogValue = DEFAULT_LEVEL,
    back_up_count: int = 10,
    maxBytes: int = 10000,
) -> None:
    """Set a file to write log to, independently from the stdout and stderr
    output chosen using :meth:`set_logging_level`.
    Parameters
    ----------
    fname : str
        Path to file to direct the output to.
    filemode : str
        'w' or 'a', defining if the file should be overwritten or appended.
    level : str
        One of ``{'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}``. This is set for the file
        independently of the console output level set by :meth:`set_logging_level`.
    """
    if filemode not in "wa":
        raise ValueError("filemode must be either 'w' or 'a'")

    # Close previous handler, if any
    if "file" in log.handlers:
        try:
            log.handlers["file"].file.close()
        except:  # pylint: disable=bare-except
            del log.handlers["file"]
            log.warning("Log file could not be closed")

    try:
        # pylint: disable=consider-using-with,unspecified-encoding
        file = open(fname, filemode)
    except:  # pylint: disable=bare-except
        log.error(f"File {fname} could not be opened")
        return

    log.handlers["file"] = LogHandler(
        Console(file=file, log_path=False), level, fname, back_up_count, maxBytes
    )


# Set default logging output
set_logging_console()
