# CLAUDE.md

Guidance for AI assistants working in this repository.

## Project overview

`osmapi` is a pure-Python wrapper around the [OpenStreetMap API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6).
It is a library (no CLI, no server), published on [PyPI](https://pypi.python.org/pypi/osmapi) and documented at
<http://osmapi.metaodi.ch> (GitHub Pages, served from the `main` branch via `docs/` + `CNAME`).

- Packaging: PEP 621 `pyproject.toml` (setuptools backend), dependencies and virtual env managed with
  [uv](https://docs.astral.sh/uv/); `uv.lock` is committed. There is no `setup.py`, `setup.cfg` or
  `requirements.txt` anymore.
- Runtime dependency: **`requests` only** (`[project] dependencies`). Do not add new runtime dependencies
  without a very good reason — everything in `[dependency-groups]` (`dev`, `docs`, `lint`, `test`) is
  dev/test tooling.
- Version constraints: runtime deps get a **lower bound only** — never cap a dependency (`<`) in a library,
  the cap propagates into every downstream resolver. Dev tools get `>=` floors at the versions currently
  locked, except `black`, `pdoc` and `Pygments`, which are pinned exactly because a bump rewrites the whole
  code base / the committed `docs/`. Constraints also matter for Dependabot: it skips dependencies declared
  without any specifier, so a new dependency needs at least a floor to be tracked.
- Supported Python: **>= 3.10** (CI matrix: 3.10, 3.11, 3.12, 3.13, 3.14).
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
.github/           dependabot.yml (weekly uv / github-actions / pre-commit updates)
pyproject.toml     packaging metadata, dependency groups, mypy config
uv.lock            the locked dev environment (committed)
.flake8            flake8 config (max-complexity, line length, E203 ignore)
```

## Architecture

`OsmApi` is composed from mixins:

```python
class OsmApi(NodeMixin, WayMixin, RelationMixin, ChangesetMixin, NoteMixin, CapabilitiesMixin):
```

Every mixin method is annotated `self: "OsmApi"` (with `from .OsmApi import OsmApi` under
`if TYPE_CHECKING:`) so mypy resolves the cross-mixin attribute access. Keep that pattern when adding methods.
The `[[tool.mypy.overrides]]` block in `pyproject.toml` disables mypy's `misc` error code per-mixin-module —
that is what makes the `self: "OsmApi"` annotation acceptable; don't "fix" it by removing the annotations.

Request/response flow for a typical call:

1. Mixin method builds the URI (`/api/0.6/...`) and calls `self._session._get/_put/_post/_delete`.
2. `http.OsmApiSession._http()` performs the request, retrying up to `MAX_RETRY_LIMIT` (5) on 5xx and on
   unexpected exceptions, sleeping 5s between attempts; 4xx and `AuthenticationMissingError` are re-raised
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

Everything runs through [uv](https://docs.astral.sh/uv/) — the `make` targets wrap `uv run`, so there is no
venv to activate manually:

```bash
./setup.sh          # just calls `make deps`
make deps           # uv sync (creates ./.venv) + uv run pre-commit install
make format         # black over osmapi examples tests
make lint           # black --check, flake8 ., mypy osmapi
make test           # pytest --cov=osmapi tests/ (in UTF-8 mode)
make coverage       # coverage run + report
make docs           # pdoc -o docs osmapi  (regenerates the committed docs/)
make build          # uv build (wheel + sdist into dist/)
./test.sh           # what CI runs: lint + test + docs + build + import from the built wheel
```

Use `uv run <cmd>` for one-off commands and `uv run --python 3.13 ...` to try another interpreter;
`uv add` / `uv add --group <group>` when a dependency really has to change (that also updates `uv.lock`).

Style rules: **black** (line length 88), flake8 with `max-complexity = 10` and `extend-ignore = E203`
(see `.flake8`). Functions that legitimately exceed the complexity limit carry `# noqa: C901` —
prefer refactoring, but the marker is accepted for the big dispatch functions.
`pre-commit` runs black, flake8 and mypy (the hook points at `--config-file=pyproject.toml`);
`make deps` installs the hooks.

## Tests

- Framework: **pytest**, run from the repo root so `tests/fixtures` resolves. Plain test functions plus
  fixtures — there are no `unittest` classes left, don't add any.
- Fixtures live in `tests/conftest.py` and are built on the `responses` library:
  - `api`, `auth_api`, `prod_api` — an `OsmApi` against the dev/prod base URL, with `_sleep` mocked out.
  - `changeset_api` — `auth_api` with changeset `OPEN_CHANGESET_ID` (1111) already open, for element writes.
  - `add_response(method, path=..., filename=..., body=..., status=..., url=...)` — registers a mocked
    response. `path` is relative to `/api/0.6`; pass `url` for anything outside it (e.g. `/api/capabilities`).
    `filename` defaults to the fixture named after the test function. Naming a `path`/`url` is what makes
    `responses` assert the request URL, so prefer it over the catch-all.
  - `assert_request_xml(request, payload)` — compares a request body against `payload` wrapped in the
    `<osm>` envelope. Use this rather than spelling out the prolog and generator string, which would
    otherwise hardcode the version number and break on every release.
  - `mock_api(...)` — an `OsmApi` backed by a `unittest.mock` session, returning `(api, session_mock)`.
    Only for tests about the HTTP layer itself (status-code mapping, the retry loop); it does **not**
    match on URL, so prefer the `responses` fixtures for everything else.
- Tests never hit the network; every HTTP interaction is backed by a fixture in `tests/fixtures/`
  (XML for parsed responses, plain text for error payloads). Add one named after the test.
- Assert on the request too (method, URL, query params, and body where relevant), not just the parsed
  result — that is what catches URI regressions.
- Error payloads are `bytes` (that is what `requests` gives you). Assert on `payload_str` for the decoded
  text, or compare against a `b"..."` literal.
- Line coverage alone over-reports here; when adding tests for a behaviour, check it actually fails when
  the behaviour is broken.

## Branches and releases

- `develop` is the integration branch and the **default target for pull requests**; `main` holds releases and
  the published documentation.
- CI (`build.yml`) runs `./test.sh` on every PR and on pushes to `main`/`develop`, across Python 3.10–3.14
  (`astral-sh/setup-uv` + `uv sync`).
- Dependabot (`.github/dependabot.yml`) opens weekly PRs against `develop` for the `uv`, `github-actions`
  and `pre-commit` ecosystems; dev-dependency bumps are grouped into a single PR, runtime bumps are not.
- The version lives **only** in `osmapi/__init__.py`; `pyproject.toml` reads it via
  `[tool.setuptools.dynamic] version = { attr = "osmapi.__version__" }`.
- Release steps (see README): bump `__version__` in `osmapi/__init__.py`, update `CHANGELOG.md`,
  run `make docs`, PR `develop` -> `main`, then publish a GitHub release/tag — `publish_python.yml`
  builds and uploads to PyPI via trusted publishing on `release: published` (or manual `workflow_dispatch`
  with a tag).
- The project follows [Semantic Versioning](http://semver.org/) and
  [Keep a Changelog](http://keepachangelog.com/); add an entry under `## [Unreleased]` for user-visible changes.

## Gotchas

- Username/password auth was shut down by OSM (July 2024) and removed from osmapi in 6.0. Authentication
  comes exclusively from the session; examples and docs use OAuth 2.0 by passing a prepared
  `requests.Session` via the `session=` parameter. OSM only accepts a bearer token in the `Authorization`
  header (`access_token_methods :from_bearer_authorization` in its Doorkeeper config) — there is no
  query-parameter variant to support.
- Don't reintroduce sniffing of `session.auth` to decide whether a request can be authenticated:
  `OsmApiSession._can_authenticate` is `True` for *any* caller-supplied session, because credentials can
  live where osmapi cannot see them (an `Authorization` header, a transport adapter, or a `Session`
  subclass adding the token per request — `requests_oauthlib.OAuth2Session` sets `session.auth` to a no-op
  lambda and injects the token in `request()`). `AuthenticationMissingError` is raised before sending only
  when osmapi built the session itself; everything else is the API's 401 -> `UnauthorizedApiError`.
  `_auth` still exists, but only to re-apply `session.auth` when the session is rebuilt between retries.
- Deprecated error names live in `errors.DEPRECATED_ERROR_NAMES` and are resolved by the module-level
  `__getattr__` of both `osmapi/errors.py` and `osmapi/__init__.py` (the star-import doesn't pick up the
  hook, hence both). `UsernamePasswordMissingError` is such an alias and is due for removal in 7.0.
- Point examples and manual testing at the dev server `https://api06.dev.openstreetmap.org`, never production.
- `docs/` is generated **and committed**; regenerate with `make docs` when docstrings change rather than
  editing the HTML.
- `_do()` mutates the `osm_data` dict it is given (drops `timestamp`, sets `changeset`, `id`, `version`).
- `self._current_changeset_id` is set by `changeset_create` and reset to `0` by `changeset_close`
  (the `changeset()` context manager wraps both). `changeset_update`, `changeset_close`, `changeset_upload`
  and every element write require it to be non-zero, otherwise `NoChangesetOpenError` is raised;
  `changeset_create` raises `ChangesetAlreadyOpenError` if one is already open.
- `black` is pinned twice — `[dependency-groups] lint` in `pyproject.toml` and `rev:` in
  `.pre-commit-config.yaml`. Bump both together, otherwise `make lint` and the hook disagree on formatting.
- Don't hand-edit `uv.lock`; change `pyproject.toml` and run `uv sync` (or use `uv add`) so the lock is
  regenerated.
