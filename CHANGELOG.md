# Change Log
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project follows [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Changed
- Only include `discussion` key in result of `ChangesetGet` if `include_discussion=True` (see issue #163, thanks [Mateusz Konieczny](https://github.com/matkoniecz))
- Update OAuth example in README using [cli-oauth2](https://github.com/Zverik/cli-oauth2) (see PR #169, thanks [Ilya Zverev](https://github.com/Zverik)

## [4.1.0] - 2024-03-19
### Added
- OAuth 2.0 example in README and in the `examples` directory

### Changed
- Check if a passed `session` is authenticated and use this instead of Username/Password, this enables OAuth 2.0 authentication

### Removed
- remove Python2 crumbs (see PR #159, thanks [Alexandre Detiste](https://github.com/a-detiste))

## [4.0.0] - 2023-07-15
### Added
- Add Python 3.11 to build
- Add pre-commit configuration for `flake8` and `black`

### Changed
- Upgrade the code with `pyupgrade` (see PR #146, thanks [Miroslav Šedivý](https://github.com/eumiro))
Miroslav Šedivý
- Replace format with f-strings to resolve issue (see PR #147, thanks [Miroslav Šedivý](https://github.com/eumiro))
- Use the `black` code style for this code base

### Removed
- **BC-Break**: Remove support for Python 3.7, new minimum version for osmapi is Python 3.8

## [3.1.0] - 2023-01-18
### Added
- New `ElementNotFoundApiError` when a 404 response comes from the API
- Raise an exception if a user tries to create a test changeset on the PROD server (see issue #66, thanks [SomeoneElseOSM](https://github.com/SomeoneElseOSM))

### Changed
- Add new `NoteAlreadyClosedApiError` exception when you try to close an already closed note (see issue #135, thanks [Mateusz Konieczny](https://github.com/matkoniecz))

### Fixed
- `NoteGets` now allows empty results i.e. it returns an empty list if no notes were found (see issue #137, thanks [Mateusz Konieczny](https://github.com/matkoniecz))

## [3.0.0] - 2022-02-12
### Added
- Add context manager `Changeset()` to open/close changesets
- Add `session` parameter to provide a custom http session object

### Changed
- Refactor code into several modules/files to improve maintainability
- Use `logging` module to log debug information

### Removed
- **BC-Break**: Remove `debug` parameter of OsmApi, replaced debug messages with `logging` module

### Fixed
- Added `python_requires` to setup.py to define Python 3.7 as minimum version

## [2.0.2] - 2021-11-24
### Changed
- Set `long_description` format to markdown

## [2.0.1] - 2021-11-24
### Added
- Add Makefile for all common tasks

### Fixed
- Long description of osmapi (now using directly the README.md)

### Changed
- Switch from nose to pytest
- Move docs to its own subdirectory

### Removed
- Remove tox configuration and dependency

## [2.0.0] - 2021-11-22
### Added
- Move from Travis CI to Github Actions
- Add more API-specific errors to catch specific errors (see issue #115, thanks [Mateusz Konieczny](https://github.com/matkoniecz)):
    - `ChangesetClosedApiError`
    - `NoteClosedApiError`
    - `VersionMismatchApiError`
    - `PreconditionFailedApiError`

### Changed
- **BC-Break**: osmapi does **not** support Python 2.7, 3.3, 3.4, 3.5 and 3.6 anymore

### Fixed
- Return an empty list in `NodeRelations`, `WayRelations`, `RelationRelations` and `NodeWays` if the returned XML is empty (thanks [FisherTsai](https://github.com/FisherTsai), see issue #117)

## [1.3.0] - 2020-10-05
### Added
- Add close() method to close the underlying http session (see issue #107)
- Add context manager to automatically open and close the http session (see issue #107)

### Fixed
- Correctly parse password file (thanks [Julien Palard](https://github.com/JulienPalard), see pull request #106)

## [1.2.2] - 2018-11-05
### Fixed
- Update PyPI password for deployment

## [1.2.1] - 2018-11-05
### Fixed
- Deployment to PyPI with Travis

## [1.2.0] - 2018-11-05
### Added
- Support Python 3.7 (thanks a lot [cclauss](https://github.com/cclauss))

### Removed
- Python 3.3 is no longer supported (EOL) 

### Changed
- Updated dependencies for Python 3.7
- Adapt README to use Python 3 syntax (thanks [cclauss](https://github.com/cclauss))

## [1.1.0] - 2017-10-11
### Added
- Raise new `XmlResponseInvalidError` if XML response from the OpenStreetMap API is invalid

### Changed
- Improved README (thanks [Mateusz Konieczny](https://github.com/matkoniecz))

## [1.0.2] - 2017-09-07
### Added
- Rais ResponseEmptyApiError if we expect a response from the OpenStreetMap API, but didn't get one

### Removed
- Removed httpretty as HTTP mock library

## [1.0.1] - 2017-09-07
### Fixed
- Make sure tests run offline

## [1.0.0] - 2017-09-05
### Added
- Officially support Python 3.5 and 3.6

### Removed
- osmapi does **not** support Python 2.6 anymore (it might work, it might not)

### Changed
- **BC-Break:** raise an exception if the requested element is deleted (previoulsy `None` has been returned)

## [0.8.1] - 2016-12-21
### Fixed
- Use setuptools instead of distutils in setup.py

## [0.8.0] - 2016-12-21
### Removed
- This release no longer supports Python 3.2, if you need it, go back to release <= 0.6.2

## Changed
- Read version from __init__.py instead of importing it in setup.py

## [0.7.2] - 2016-12-21
### Fixed
- Added 'requests' as a dependency to setup.py to fix installation problems

## [0.7.1] - 2016-12-12
### Changed
- Catch OSError in setup.py to avoid installation errors

## [0.7.0] - 2016-12-07
### Changed
- Replace the old httplib with requests library (thanks a lot [Austin Hartzheim](http://austinhartzheim.me/)!)
- Use format strings instead of ugly string concatenation
- Fix unicode in changesets (thanks a lot to [MichaelVL](https://github.com/MichaelVL)!)

## [0.6.2] - 2016-01-04
### Changed
- Re-arranged README
- Make sure PyPI releases are only created when a release has been tagged on GitHub

## [0.6.1] - 2016-01-04
### Changed
- The documentation is now available at a new domain: http://osmapi.metaodi.ch, the previous provider does no longer provide this service

## [0.6.0] - 2015-05-26
### Added
- SSL support for the API calls (thanks [Austin Hartzheim](http://austinhartzheim.me/)!)
- Run tests on Python 3.4 as well
- A bunch of new *Error classes (see below)
- Dependency to 'Pygments' to enable syntax highlighting for [online documentation](http://osmapi.divshot.io)
- [Contributing guidelines](https://github.com/metaodi/osmapi/blob/master/CONTRIBUTING.md) 

### Changed
- Changed generic `Exception` with more specific ones, so a client can catch those and react accordingly (no BC-break!)

## [0.5.0] - 2015-01-03
### Changed
- BC-break: all dates are now parsed as datetime objects

### Added
- Implementation for changeset discussions (ChangesetComment, ChangesetSubscribe, ChangesetUnsubscribe)
- When (un)subscribing to a changeset, there are two special errors `AlreadySubscribedApiError` and `NotSubscribedApiError` to check for
- The ChangesetGet method got a new parameter `include_discussion` to determine wheter or not changeset discussion should be in the response

## [0.4.2] - 2015-01-01
### Fixed
- Result of `NodeWay` is now actually parsed as a `way`

### Added
- Lots of method comments for documentation

### Changed
- Update to pdoc 0.3.1 which changed the appearance of the online docs

## [0.4.1] - 2014-10-08
### Changed
- Parse dates in notes as `datetime` objects

## [0.4.0] - 2014-10-07
### Added
- Release for OSM Notes API
- Generation of online documentation (http://osmapi.divshot.io)

## [0.3.1] - 2014-06-21
### Fixed
- Hotfix release of Python 3.x (base64)

## [0.3.0] - 2014-05-20
### Added
- Support for Python 3.x
- Use `tox` to run tests against multiple versions of Python

## [0.2.26] - 2014-05-02
### Fixed
- Fixed notes again

## [0.2.25] - 2014-05-02
### Fixed
- Unit tests for basic functionality
- Fixed based on the unit tests (previously undetected bugs)

## [0.2.24] - 2014-01-07
### Fixed
- Fixed notes

## [0.2.23] - 2014-01-03
### Changed
- Hotfix release

## [0.2.22] - 2014-01-03
### Fixed
- Fixed README.md not found error during installation

## [0.2.21] - 2014-01-03
### Changed
- Updated description

## [0.2.20] - 2014-01-01
### Added
- First release of PyPI package "osmapi"

## [0.2.19] - 2014-01-01
### Changed
- Inital version from SVN (http://svn.openstreetmap.org/applications/utils/python_lib/OsmApi/OsmApi.py)
- Move to GitHub

## 0.2.19 - 2010-05-24
### Changed
- Add debug message on ApiError

## 0.2.18 - 2010-04-20
### Fixed
- Fix ChangesetClose and _http_request

## 0.2.17 - 2010-01-02
### Added
- Capabilities implementation

## 0.2.16 - 2010-01-02
### Changed
- ChangesetsGet by Alexander Rampp

## 0.2.15 - 2009-12-16
### Fixed
- xml encoding error for < and >

## 0.2.14 - 2009-11-20
### Changed
- changesetautomulti parameter

## 0.2.13 - 2009-11-16
### Changed
- modify instead update for osc

## 0.2.12 - 2009-11-14
### Added
- raise ApiError on 4xx errors

## 0.2.11 - 2009-10-14
### Fixed
- unicode error on ChangesetUpload

## 0.2.10 - 2009-10-14
### Added
- RelationFullRecur definition

## 0.2.9  - 2009-10-13
### Added
- automatic changeset management
- ChangesetUpload implementation

## 0.2.8  - 2009-10-13
### Changed
- *(Create|Update|Delete) use not unique _do method

## 0.2.7  - 2009-10-09
### Added
- implement all missing functions except ChangesetsGet and GetCapabilities

## 0.2.6  - 2009-10-09
### Changed
- encoding clean-up

## 0.2.5  - 2009-10-09
### Added
- implements NodesGet, WaysGet, RelationsGet, ParseOsm, ParseOsc

## 0.2.4  - 2009-10-06 clean-up
### Changed
- clean-up

## 0.2.3  - 2009-09-09 
### Changed
- keep http connection alive for multiple request
- (Node|Way|Relation)Get return None when object have been deleted (raising error before)

## 0.2.2  - 2009-07-13
### Added
- can identify applications built on top of the lib

## 0.2.1  - 2009-05-05
### Changed
- some changes in constructor

## 0.2    - 2009-05-01
### Added
- initial import


# Categories
- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for once-stable features removed in upcoming releases.
- `Removed` for deprecated features removed in this release.
- `Fixed` for any bug fixes.
- `Security` to invite users to upgrade in case of vulnerabilities.

[Unreleased]: https://github.com/metaodi/osmapi/compare/v4.1.0...HEAD
[4.1.0]: https://github.com/metaodi/osmapi/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/metaodi/osmapi/compare/v3.1.0...v4.0.0
[3.1.0]: https://github.com/metaodi/osmapi/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/metaodi/osmapi/compare/v2.0.2...v3.0.0
[2.0.2]: https://github.com/metaodi/osmapi/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/metaodi/osmapi/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/metaodi/osmapi/compare/v1.3.0...v2.0.0
[1.3.0]: https://github.com/metaodi/osmapi/compare/v1.2.2...v1.3.0
[1.2.2]: https://github.com/metaodi/osmapi/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/metaodi/osmapi/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/metaodi/osmapi/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/metaodi/osmapi/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/metaodi/osmapi/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/metaodi/osmapi/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/metaodi/osmapi/compare/v0.8.1...v1.0.0
[0.8.1]: https://github.com/metaodi/osmapi/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/metaodi/osmapi/compare/v0.7.2...v0.8.0
[0.7.2]: https://github.com/metaodi/osmapi/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/metaodi/osmapi/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/metaodi/osmapi/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/metaodi/osmapi/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/metaodi/osmapi/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/metaodi/osmapi/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/metaodi/osmapi/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/metaodi/osmapi/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/metaodi/osmapi/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/metaodi/osmapi/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/metaodi/osmapi/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/metaodi/osmapi/compare/v0.2.26...v0.3.0
[0.2.26]: https://github.com/metaodi/osmapi/compare/v0.2.25...v0.2.26
[0.2.25]: https://github.com/metaodi/osmapi/compare/v0.2.24...v0.2.25
[0.2.24]: https://github.com/metaodi/osmapi/compare/v0.2.23...v0.2.24
[0.2.23]: https://github.com/metaodi/osmapi/compare/v0.2.22...v0.2.23
[0.2.22]: https://github.com/metaodi/osmapi/compare/v0.2.21...v0.2.22
[0.2.21]: https://github.com/metaodi/osmapi/compare/v0.2.20...v0.2.21
[0.2.20]: https://github.com/metaodi/osmapi/compare/v0.2.19...v0.2.20
[0.2.19]: https://github.com/metaodi/osmapi/releases/tag/v0.2.19

