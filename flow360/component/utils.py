"""
Utility functions
"""
from functools import wraps
import uuid

from ..log import log

# pylint: disable=redefined-builtin
def is_valid_uuid(id, ignore_none=False):
    """
    Checks if id is valid
    """
    if id is None and ignore_none:
        return
    try:
        uuid.UUID(str(id))
    except Exception as exc:
        raise ValueError(f"{id} is not a valid UUID.") from exc


def beta_feature(feature_name: str):
    def wrapper(func):
        @wraps(func)
        def wrapper_func(*args, **kwargs):
            log.warning(f'{feature_name} is a beta feature.')
            value = func(*args, **kwargs)
            return value
        return wrapper_func
    return wrapper




def _get_value_or_none(callable):
    try:
        return callable()
    except:
        return None    