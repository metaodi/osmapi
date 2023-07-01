import time
import logging
import requests

from . import errors


logger = logging.getLogger(__name__)


class OsmApiSession:

    MAX_RETRY_LIMIT = 5
    """Maximum retries if a call to the remote API fails (default: 5)"""

    def __init__(self, base_url, created_by, auth=None, session=None):
        self._api = base_url
        self._created_by = created_by
        self._auth = auth

        self._http_session = session
        self._session = self._get_http_session()

    def close(self):
        if self._session:
            self._session.close()

    def _http_request(self, method, path, auth, send, return_value=True):  # noqa
        """
        Returns the response generated by an HTTP request.

        `method` is a HTTP method to be executed
        with the request data. For example: 'GET' or 'POST'.
        `path` is the path to the requested resource relative to the
        base API address stored in self._api. Should start with a
        slash character to separate the URL.
        `auth` is a boolean indicating whether authentication should
        be preformed on this request.
        `send` contains additional data that might be sent in a
        request.
        `return_value` indicates wheter this request should return
        any data or not.

        If the username or password is missing,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.

        If the response status code indicates an error,
        `OsmApi.ApiError` is raised.
        """
        msg = (
            "%s %s %s"
            % (time.strftime("%Y-%m-%d %H:%M:%S"), method, path)
        )
        logger.debug(msg)

        # Add API base URL to path
        path = self._api + path

        if auth and not self._auth:
            raise errors.UsernamePasswordMissingError("Username/Password missing")

        response = self._session.request(
            method,
            path,
            data=send
        )
        if response.status_code != 200:
            payload = response.content.strip()
            if response.status_code == 404:
                raise errors.ElementNotFoundApiError(
                    response.status_code,
                    response.reason,
                    payload
                )
            elif response.status_code == 410:
                raise errors.ElementDeletedApiError(
                    response.status_code,
                    response.reason,
                    payload
                )
            raise errors.ApiError(response.status_code, response.reason, payload)
        if return_value and not response.content:
            raise errors.ResponseEmptyApiError(
                response.status_code,
                response.reason,
                ''
            )

        msg = (
            "%s %s %s"
            % (time.strftime("%Y-%m-%d %H:%M:%S"), method, path)
        )
        logger.debug(msg)
        return response.content

    def _http(self, cmd, path, auth, send, return_value=True):  # noqa
        i = 0
        while True:
            i += 1
            try:
                return self._http_request(
                    cmd,
                    path,
                    auth,
                    send,
                    return_value=return_value
                )
            except errors.ApiError as e:
                if e.status >= 500:
                    if i == self.MAX_RETRY_LIMIT:
                        raise
                    if i != 1:
                        self._sleep()
                    self._session = self._get_http_session()
                else:
                    raise
            except Exception as e:
                logger.error(e)
                if i == self.MAX_RETRY_LIMIT:
                    if isinstance(e, errors.OsmApiError):
                        raise
                    raise errors.MaximumRetryLimitReachedError(
                        "Give up after %s retries" % i
                    )
                if i != 1:
                    self._sleep()
                self._session = self._get_http_session()

    def _get_http_session(self):
        """
        Creates a requests session for connection pooling.
        """
        if self._http_session:
            session = self._http_session
        else:
            session = requests.Session()

        session.auth = self._auth
        session.headers.update({
            'user-agent': self._created_by
        })
        return session

    def _sleep(self):
        time.sleep(5)

    def _get(self, path):
        return self._http('GET', path, False, None)

    def _put(self, path, data, return_value=True):
        return self._http('PUT', path, True, data, return_value=return_value)

    def _post(self, path, data, optionalAuth=False, forceAuth=False):
        # the Notes API allows certain POSTs by non-authenticated users
        auth = (optionalAuth and self._auth)
        if forceAuth:
            auth = True
        return self._http('POST', path, auth, data)

    def _delete(self, path, data):
        return self._http('DELETE', path, True, data)