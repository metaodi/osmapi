"""
Fetch user history of changes from OpenStreetMap.

If there are more than 100 changes, `osmapi` will repeat request till all
changes are be fetched.

Also script can store the history data into "pickle" file format, so it is
possible to load it again without fetching OSM API.

Example of storing the history data into different formats:
python3 ./examples/fetch_user_history.py --username 'My%20user' --loglevel INFO --filename /tmp/MyHistory.pickle
python3 ./examples/fetch_user_history.py --username 'My%20user' --loglevel INFO --load-pickle /tmp/MyHistory.pickle --filename /tmp/1.csv
python3 ./examples/fetch_user_history.py --username 'My%20user' --loglevel INFO --load-pickle /tmp/MyHistory.pickle --filename /tmp/1.json

See
https://wiki.openstreetmap.org/wiki/API_v0.6#Query:_GET_/api/0.6/changesets
and
https://wiki.openstreetmap.org/wiki/API_v0.6#Capabilities:_GET_/api/capabilities
for more details.
"""

import datetime
import argparse
import logging
import csv
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
        metavar="FILENAME",
        help="File to store, supported formats: JSON, CSV or pickle (selected by extension).",
    )
    parser.add_argument(
        "--load-pickle",
        metavar="FILENAME",
        help="Instead of fetching the history data from OSM API, use previously stored 'pickle' file.",
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


def load_pickle(filename: str):
    """
    Load "pickle" file, stored beforehand by `save_file`.
    To have possibility to play with data without stressing out OSM API server.
    """
    with open(filename, "rb") as f:
        return pickle.load(f)


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
    elif filename.endswith(".csv"):
        with open(filename, encoding="utf-8", mode="w", newline="") as f:
            fieldnames = ["id", "created_at", "tag"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for i in history:
                writer.writerow(history[i])
    else:
        logging.error("Use known file extension to save the file: .json, .csv or .pickle")


def convert_data(history):
    # PUT YOUR CODE HERE IF NEEDED
    pass


def main():
    config = parse_args()
    logging.debug("Script started!")
    if config.load_pickle:
        logging.info(
            "Instead of using OSM API, loading 'pickle' file '%s'", config.load_pickle
        )
        history = load_pickle(config.load_pickle)
    else:
        api = osmapi.OsmApi()
        logging.info("Limits (capabilities): %s", api.Capabilities()["changesets"])
        if config.start:
            history = api.UserHistory(
                UserId=config.username, limit=config.limit, TimeFrom=config.start
            )
        else:
            history = api.UserHistory(UserId=config.username, limit=config.limit)
    convert_data(history)
    save_file(config.filename, history)
    logging.debug("Script finished!")


if __name__ == "__main__":
    main()
