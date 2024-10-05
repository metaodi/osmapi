"""
Fetch user history of changes from OpenStreetMap.

If there are more than 100 changes, `osmapi` will repeat request till all
changes will be fetched.

See
https://wiki.openstreetmap.org/wiki/API_v0.6#Query:_GET_/api/0.6/changesets
and
https://wiki.openstreetmap.org/wiki/API_v0.6#Capabilities:_GET_/api/capabilities
for more details.
"""

import datetime
import argparse
import logging
import json
import pickle
import osmapi


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--username",
        required=True,
        help="OpenStreetMap username. Should be url-encoded if has special characters.",
    )
    parser.add_argument(
        "--filename",
        help="File to store, supported formats: JSON and pickle (selected by extension).",
    )
    parser.add_argument(
        "--api",
        default="https://api.openstreetmap.org/api/0.6/",
        help="Set OpenStreetMap API URL. Use https://master.apis.dev.openstreetmap.org/api/0.6/ for experiments.",
    )
    parser.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        # Can't use `datetime.date` here because of error in `osmapi.UserHistory`:
        # TypeError: can't compare datetime.datetime to datetime.date
        type=datetime.datetime.fromisoformat,
        help="History start date (by default, fetch everything)",
    )
    parser.add_argument(
        "--limit",
        default=0,
        metavar="INT",
        type=int,
        help="0 is unlimited. The result will probably be more than limit",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.loglevel),
        format="%(levelname)s:%(funcName)s:%(message)s",
    )
    logging.debug("All parsed arguments:")
    for arg, value in sorted(vars(args).items()):
        logging.debug("Argument %s: %s", arg, value)
    return args


def save_file(filename: str, history: dict[dict]):
    """
    Handle storing a file in different formats, depending on filename extension.
    If no filename provided, print to STDOUT.
    """
    logging.info("Items in history: %s", len(history))
    if not filename:
        for k, v in history.items():
            print(k, ":", v)
    elif filename.endswith(".json"):
        with open(filename, encoding="utf-8", mode="w") as f:
            # `default=str` — to avoid an error
            # "Object of type datetime is not JSON serializable"
            json.dump(history, f, indent=4, default=str)
    elif filename.endswith(".pickle"):
        with open(filename, mode="wb") as f:
            pickle.dump(history, f)
    else:
        logging.error("Use known file extension to save the file.")


def main():
    config = parse_args()
    logging.debug("Script started!")
    api = osmapi.OsmApi()
    logging.warning("Limits (capabilities): %s", api.Capabilities()["changesets"])
    if config.start:
        history = api.UserHistory(
            UserId=config.username, limit=config.limit, TimeFrom=config.start
        )
    else:
        history = api.UserHistory(UserId=config.username, limit=config.limit)
    save_file(config.filename, history)
    logging.debug("Script finished!")


if __name__ == "__main__":
    main()
