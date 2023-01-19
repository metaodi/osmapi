import osmapi
from dotenv import load_dotenv, find_dotenv
import os
from pprint import pprint

load_dotenv(find_dotenv())
user = os.getenv("OSM_USER")
pw = os.getenv("OSM_PASS")

api = osmapi.OsmApi(
    api="https://api06.dev.openstreetmap.org", username=user, password=pw
)
empty_notes = api.NotesGet(
    -93.8472901, 35.9763601, -80, 36.176360100000004, limit=1, closed=0
)
pprint(empty_notes)


# create note and then search for it
note = api.NoteCreate(
    {
        "lat": 47.3383501,
        "lon": 8.5339522,
        "text": "test note",
    }
)
test_notes = api.NotesGet(8.527504, 47.337063, 8.540679, 47.341673, limit=1, closed=0)
pprint(test_notes)


api.NoteComment(note["id"], "Another comment")
api.NoteClose(note["id"], "Close this test note")


# try to close an already closed note
try:
    api.NoteClose(note["id"], "Close the note again")
except osmapi.NoteAlreadyClosedApiError:
    print("")
    print(f"The note {note['id']} has already been closed")

# try to comment on closed note
try:
    api.NoteComment(note["id"], "Just a comment")
except osmapi.NoteAlreadyClosedApiError:
    print("")
    print(f"The note {note['id']} is closed, comment no longer possible")
