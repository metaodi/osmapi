# CLAUDE.md

Guidance for AI assistants working in this repository.

## Project overview

`osmapi` is a pure-Python wrapper around the [OpenStreetMap API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6).
It is a library (no CLI, no server), published on [PyPI](https://pypi.python.org/pypi/osmapi) and documented at
<http://osmapi.metaodi.ch> (GitHub Pages, served from the `main` branch via `docs/` + `CNAME`).

- Runtime dependency: **`requests` only** (`setup.py` `install_requires`). Do not add new runtime dependencies
  without a very good reason — everything else in `test-requirements.txt` is dev/test tooling.
- Supported Python: **>= 3.9** (CI matrix: 3.9, 3.10, 3.11, 3.12).
- License: GPLv3. Originally written by Etienne Chové, maintained by Stefan Oderbolz (metaodi).

## Repository layout

```
osmapi/            the package
  __init__.py      __version__ + star-imports of OsmApi and errors
  OsmApi.py        the OsmApi class: __init__, context manager, and the private
                   _do()/_add_changeset_data()/_assign_id_and_version()
  node.py          NodeMixin        (node_get, node_create, nodes_get, ...)
  way.py           WayMixin         (way_get, way_full, ways_get, ...)
  relation.py      RelationMixin    (relation_get, relation_full_recur, ...)
  changeset.py     ChangesetMixin   (changeset() context manager, changeset_upload, ...)
  note.py          NoteMixin        (notes_get, note_create, note_close, ...)
  capabilities.py  CapabilitiesMixin (capabilities, map)
  http.py          OsmApiSession — requests session, retries, HTTP-status -> error mapping
  dom.py           minidom parsing helpers (dom_parse_node/way/relation/changeset/note)
  parser.py        parse_osm / parse_osc / parse_notes (whole-document parsers)
  xmlbuilder.py    _xml_build / _xml_encode — request XML generation
  errors.py        exception hierarchy
tests/             pytest suite + tests/fixtures/*.xml recorded API responses
examples/          runnable usage examples (oauth2, changesets, notes, timeout, ...)
docs/              pdoc-generated HTML, committed to the repo (published via GitHub Pages)
.github/workflows/ build.yml (CI) and publish_python.yml (PyPI release)
```

## Architecture

`OsmApi` is composed from mixins:

```python
class OsmApi(NodeMixin, WayMixin, RelationMixin, ChangesetMixin, NoteMixin, CapabilitiesMixin):
```

Every mixin method is annotated `self: "OsmApi"` (with `from .OsmApi import OsmApi` under
`if TYPE_CHECKING:`) so mypy resolves the cross-mixin attribute access. Keep that pattern when adding methods.
`setup.cfg` disables mypy's `misc` error code per-mixin-module — that is what makes the `self: "OsmApi"`
annotation acceptable; don't "fix" it by removing the annotations.

Request/response flow for a typical call:

1. Mixin method builds the URI (`/api/0.6/...`) and calls `self._session._get/_put/_post/_delete`.
2. `http.OsmApiSession._http()` performs the request, retrying up to `MAX_RETRY_LIMIT` (5) on 5xx and on
   unexpected exceptions, sleeping 5s between attempts; 4xx and `UsernamePasswordMissingError` are re-raised
   immediately. Status codes map to typed errors (401 -> `UnauthorizedApiError`, 404 -> `ElementNotFoundApiError`,
   410 -> `ElementDeletedApiError`, empty body -> `ResponseEmptyApiError`, otherwise `ApiError`).
3. The mixin parses bytes with `dom.OsmResponseToDom(data, tag=..., single=..., allow_empty=...)` and then a
   `dom.dom_parse_*` helper, or with a `parser.parse_*` function for full documents.
4. Writes go through `OsmApi._do(action, osm_type, osm_data)`, which requires an open changeset
   (`self._current_changeset_id`), serializes via `xmlbuilder._xml_build`, and translates 409/412 into
   `ChangesetClosedApiError` / `VersionMismatchApiError` / `PreconditionFailedApiError`.

Data is plain `dict`s throughout — there are no model classes. Conventions (documented in the `OsmApi.py`
module docstring, keep it in sync): keys are unicode, `changeset`/`version`/`uid` are ints, `tag` is a dict,
node `lat`/`lon` are floats, way `nd` is a list of ints, relation `member` is a list of
`{"role": ..., "ref": ..., "type": ...}` dicts, and timestamps are parsed into `datetime` objects by `dom._parse_date`.

## Naming convention (important)

The public API is `snake_case`. The `CamelCase` names (`NodeGet`, `ChangesetCreate`, ...) were deprecated
in **5.0** and **removed in 6.0** — there are no aliases left in `OsmApi.py`.

When you add a new public method:

- implement it in the appropriate mixin with a `snake_case` name and `snake_case` parameters;
- do **not** add a `CamelCase` alias, not even for a method that used to have one.

## Docstrings

Docstrings are the documentation — `make docs` runs `pdoc` over them and writes `docs/`. Follow the existing
style: describe the returned dict inline using pdoc's fenced form

```
    #!python
    {
        'id': id of node,
        ...
    }
```

and list every exception the method can raise ("If the requested element has been deleted,
`OsmApi.ElementDeletedApiError` is raised.").

## Development workflow

```bash
./setup.sh          # create ./pyenv venv, install deps + this package editable
make deps           # install requirements + test-requirements, install pre-commit hooks
make format         # black over osmapi examples tests *.py
make lint           # black --check, flake8, mypy osmapi
make test           # pytest --cov=osmapi tests/
make coverage       # coverage run + report
make docs           # pdoc -o docs osmapi  (regenerates the committed docs/)
./test.sh           # what CI runs: lint + test + docs + install into a fresh virtualenv
```

Style rules: **black** (line length 88), flake8 with `max-complexity = 10` and `extend-ignore = E203`
(see `setup.cfg`). Functions that legitimately exceed the complexity limit carry `# noqa: C901` —
prefer refactoring, but the marker is accepted for the big dispatch functions.
`pre-commit` runs black, flake8 and mypy; `make deps` installs the hooks.

Note: `CONTRIBUTING.md` is outdated (it mentions `nosetests`, `tox` and Travis CI). The commands above and
`.github/workflows/build.yml` are the source of truth.

## Tests

- Framework: **pytest**, run from the repo root so `tests/fixtures` resolves.
- Two coexisting styles:
  - Legacy `unittest` classes inheriting `tests/osmapi_test.TestOsmApi` (node, way, relation, notes,
    capabilities, dom, helper tests). `self._session_mock(auth=..., filenames=..., status=...)` swaps in a
    mocked `requests` session; with no `filenames` it loads `tests/fixtures/<test_method_name>.xml`.
  - Modern pytest fixtures in `tests/conftest.py` (`api`, `auth_api`, `prod_api`, `add_response`,
    `mocked_responses`, `file_content`) built on the `responses` library — used by `tests/changeset_test.py`.
    **Prefer this style for new tests.** `add_response(method, path=..., filename=...)` defaults to the
    fixture named after the test function.
- Tests never hit the network; every HTTP interaction is backed by an XML fixture in `tests/fixtures/`.
  When adding a test that needs a new response, add the fixture file named after the test.
- Assert on the request too (method, URL, and body where relevant), not just the parsed result — that is what
  catches URI regressions.

## Branches and releases

- `develop` is the integration branch and the **default target for pull requests**; `main` holds releases and
  the published documentation.
- CI (`build.yml`) runs `./test.sh` on every PR and on pushes to `main`/`develop`, across Python 3.9–3.12.
- Release steps (see README): bump `__version__` in `osmapi/__init__.py`, update `CHANGELOG.md`,
  run `make docs`, PR `develop` -> `main`, then publish a GitHub release/tag — `publish_python.yml`
  builds and uploads to PyPI via trusted publishing on `release: published` (or manual `workflow_dispatch`
  with a tag).
- The project follows [Semantic Versioning](http://semver.org/) and
  [Keep a Changelog](http://keepachangelog.com/); add an entry under `## [Unreleased]` for user-visible changes.

## Gotchas

- Username/password auth is deprecated by OSM (shut down July 2024). New examples and docs should use
  OAuth 2.0 by passing a prepared `requests.Session` via the `session=` parameter.
- Point examples and manual testing at the dev server `https://api06.dev.openstreetmap.org`, never production.
- `docs/` is generated **and committed**; regenerate with `make docs` when docstrings change rather than
  editing the HTML.
- `_do()` mutates the `osm_data` dict it is given (drops `timestamp`, sets `changeset`, `id`, `version`).
- `self._current_changeset_id` is set by `changeset_create` and reset to `0` by `changeset_close`
  (the `changeset()` context manager wraps both). `changeset_update`, `changeset_close`, `changeset_upload`
  and every element write require it to be non-zero, otherwise `NoChangesetOpenError` is raised;
  `changeset_create` raises `ChangesetAlreadyOpenError` if one is already open.
- mypy prints a warning that `python_version = 3.9` in `setup.cfg` is unsupported by the installed mypy —
  it still succeeds; that is expected, not a failure.
