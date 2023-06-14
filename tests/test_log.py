import os
from flow360.log import log, set_logging_level, set_logging_file

set_logging_level("DEBUG")
set_logging_file("test_logs/test_file", "a", "DEBUG", 5, 500)


def test_debug():
    log.debug("Debug log")
    log.debug("Debug log string %s， number %d", "arg", 1)


def test_info():
    log.info("Basic info")
    log.info("Basic info string %s， number %d", "arg", 1)


def test_warning():
    log.warning("Warning log")
    log.warning("Warning log string %s， number %d", "arg", 1)


def test_error():
    log.error("Error log")
    log.error("Error log string %s， number %d", "arg", 1)


def test_critical():
    log.critical("Critical log string %s， number %d", "arg", 1)


def clean_up():
    for filename in os.listdir("./test_logs"):
        file_path = os.path.join("./test_logs", filename)
        if os.path.isfile(file_path):
            # Remove the file
            os.remove(file_path)


test_debug()
test_info()
test_warning()
test_error()
test_critical()
clean_up()
