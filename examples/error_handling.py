from dotenv import load_dotenv, find_dotenv
from oauthcli import OpenStreetMapDevAuth
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
import logging
import os
import osmapi
import requests
import subprocess
import sys
import urllib3


load_dotenv(find_dotenv())

# logging setup
log = logging.getLogger(__name__)
loglevel = logging.DEBUG
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    level=loglevel,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

# shut up DEBUG messages of specific loggers
logging.getLogger(osmapi.dom.__name__).setLevel(logging.INFO)
logging.getLogger(urllib3.__name__).setLevel(logging.INFO)


def clear_screen():
    # check and make call for specific operating system
    _ = subprocess.call("clear" if os.name == "posix" else "cls")


# The error handling with osmapi is very easy, simply catch the
# exception for the specific case you want to handle.
# - All osmapi excepctions are child classes of osmapi.OsmApiError
# - Errors that result from the communication with the OSM server osmapi.ApiError
# - There are a number of subclasses to differantiate the different errors
# - catch more specific errors first, then use more general error classes

# Upload data to OSM without a changeset
log.debug("Try to write data to OSM without a changeset")
api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")
try:
    node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
except osmapi.NoChangesetOpenError as e:
    log.exception(e)
    log.debug("There is no open changeset")
input("Press Enter to continue...")
clear_screen()


# wrong server: ConnectionError
log.debug("Connect to wrong server...")
api = osmapi.OsmApi(api="https://invalid.server.name")
try:
    api.ChangesetGet(123)
except osmapi.ConnectionApiError as e:
    log.exception(e)
    log.debug("Error connecting to server")
input("Press Enter to continue...")
clear_screen()


# changeset not found: ElementNotFoundApiError
log.debug("Request non-existent changeset id...")
api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")
try:
    api.ChangesetGet(111111111111)
except osmapi.ElementNotFoundApiError as e:
    log.exception(e)
    log.debug("Changeset not found")
input("Press Enter to continue...")
clear_screen()


# unauthorized request
log.debug("Try to add data with wrong authorization")
try:
    s = requests.Session()
    s.auth = ("user", "pass")
    api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", session=s)
    with api.Changeset({"comment": "My first test"}) as changeset_id:
        node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
except osmapi.UnauthorizedApiError as e:
    log.exception(e)
    log.debug("Unauthorized to make this request")
input("Press Enter to continue...")
clear_screen()

# request without auhorization
log.debug("Try to add data without authorization")
try:
    api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")
    with api.Changeset({"comment": "My first test"}) as changeset_id:
        node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
except osmapi.UsernamePasswordMissingError as e:
    log.exception(e)
    log.debug("Username/Password or authorization missing")
input("Press Enter to continue...")
clear_screen()


# a more or less complete "real-life" example
client_id = os.getenv("OSM_OAUTH_CLIENT_ID")
client_secret = os.getenv("OSM_OAUTH_CLIENT_SECRET")

try:
    auth = OpenStreetMapDevAuth(
        client_id, client_secret, ["write_api", "write_notes"]
    ).auth_code()
except OAuth2Error as e:
    log.exception(e)
    log.debug("An OAuth2 error occured")
    sys.exit(1)

try:
    api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", session=auth.session)
    with api.Changeset({"comment": "My first test"}) as changeset_id:
        log.debug(f"Part of Changeset {changeset_id}")
        node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
        log.debug(node1)

    # get all the info from the closed changeset
    changeset = api.ChangesetGet(changeset_id)
    log.debug(changeset)
    exit_code = 0
except osmapi.ConnectionApiError as e:
    log.debug(f"Connection error: {str(e)}")
    exit_code = 1
    # display error for user, try again?
except osmapi.ElementNotFoundApiError as e:
    log.debug(f"Changeset not found: {str(e)}")
    exit_code = 1
except osmapi.ApiError as e:
    log.debug(f"Error on the API side: {str(e)}")
    exit_code = 1
except osmapi.OsmApiError as e:
    log.debug(f"Some other error: {str(e)}")
    exit_code = 1
finally:
    log.debug(f"Exit code: {exit_code}")
    sys.exit(exit_code)
