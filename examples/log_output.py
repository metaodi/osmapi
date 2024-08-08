import osmapi
import logging
from pprint import pformat
import urllib3

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


api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")
node1 = api.NodeGet("1111")
log.debug(pformat(node1))
