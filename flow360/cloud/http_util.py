"""
http utils. Example:
http.get(path)
"""

from functools import wraps

import requests

from ..environment import Env
from ..exceptions import (
    Flow360AuthorisationError,
    Flow360WebError,
    Flow360WebNotFoundError,
)
from ..log import log
from ..user_config import UserConfig
from ..version import __version__
from .security import api_key


def api_key_auth(request):
    """
    Set the authentication.
    :param request:
    :return:
    """
    key = api_key()
    if not key:
        if Env.current.name == "dev":
            raise Flow360AuthorisationError(
                "API key not found for env=dev, please set it by commandline: flow360 configure --dev."
            )
        if Env.current.name == "uat":
            raise Flow360AuthorisationError(
                "API key not found for env=uat, please set it by commandline: flow360 configure --uat."
            )
        raise Flow360AuthorisationError(
            f"API key not found for profile={UserConfig.profile}, please set it by commandline: flow360 configure."
        )
    request.headers["simcloud-api-key"] = key
    request.headers["flow360-python-version"] = __version__
    if Env.impersonate:
        request.headers["FLOW360ACCESSUSER"] = Env.impersonate
    return request


def http_interceptor(func):
    """
    Intercept the response and raise an exception if the status code is not 200.
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """A wrapper function"""

        # Extend some capabilities of func
        log.debug(f"call: {func.__name__}({args}, {kwargs})")

        resp = func(*args, **kwargs)

        log.debug(f"response: {resp}")

        if resp.status_code == 400:
            raise Flow360WebError(
                f"Web {args[1]}: Bad request error: {resp.json()['error']}",
                auxiliary_json=resp.json(),
            )

        if resp.status_code == 401:
            raise Flow360AuthorisationError(
                f"Unauthorized. Seems your APIKEY is invalid. Check it on {Env.current.web_url} in account section."
            )

        if resp.status_code == 404:
            raise Flow360WebNotFoundError(f"Web {args[1]}: Not found error: {resp.json()}")

        if resp.status_code == 200:
            try:
                result = resp.json()
                return result.get("data")
            except ValueError:
                # Handle the case where the response does not contain JSON data
                return None

        raise Flow360WebError(f"Web {args[1]}: Unexpected response error: {resp.status_code}")

    return wrapper


class Http:
    """
    Http util class.
    """

    def __init__(self, session: requests.Session):
        self.session = session

    @http_interceptor
    def portal_api_get(self, path: str, json=None, params=None):
        """
        Get the resource.
        :param path:
        :param json:
        :return:
        """
        return self.session.get(
            url=Env.current.get_portal_real_url(path), json=json, params=params, auth=api_key_auth
        )

    @http_interceptor
    def get(self, path: str, json=None, params=None):
        """
        Get the resource.
        :param path:
        :param json:
        :return:
        """
        return self.session.get(
            url=Env.current.get_real_url(path), json=json, params=params, auth=api_key_auth
        )

    @http_interceptor
    def post(self, path: str, json=None):
        """
        Create the resource.
        :param path:
        :param json:
        :return:
        """
        return self.session.post(Env.current.get_real_url(path), json=json, auth=api_key_auth)

    @http_interceptor
    def put(self, path: str, json):
        """
        Update the resource.
        :param path:
        :param json:
        :return:
        """
        return self.session.put(Env.current.get_real_url(path), json=json, auth=api_key_auth)

    @http_interceptor
    def delete(self, path: str):
        """
        Delete the resource.
        :param path:
        :return:
        """
        return self.session.delete(Env.current.get_real_url(path), auth=api_key_auth)

    @http_interceptor
    def patch(self, path: str, json=None):
        """
        Patch the resource.
        :param path:
        :param json:
        :return:
        """
        return self.session.patch(Env.current.get_real_url(path), json=json, auth=api_key_auth)


http = Http(requests.Session())
