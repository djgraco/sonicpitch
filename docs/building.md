# Building Global Sonic Pitch

## Prerequisites

- Git, if you want to work with the repository history.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Python 3.13. uv can install it automatically if needed.
- GNU gettext tools: `msgfmt`, `xgettext` and `msgmerge` available on PATH.
  On Windows, use the [gettext Windows builds](https://mlocati.github.io/articles/gettext-iconv-windows.html).
  On Debian or Ubuntu, install the `gettext` package.

Python packages are pinned in `pyproject.toml` and resolved with hashes in
`uv.lock`. The project is a collection of build tools, not a Python library
to install into NVDA. Build Python is separate from NVDA's own runtime.
The placeholder version `0.0.0` in `pyproject.toml` identifies only this virtual
tooling project; the actual add-on version is defined in `buildVars.py`.

## Build from a checkout

Run these commands from the repository root:

1. `uv sync --locked`
2. `uv run --locked scons pot`
3. `uv run --locked python tools/check_project.py`
4. `uv run --locked scons`
5. `uv run --locked python tools/check_project.py --package --write-checksum`

The result is `globalSonicPitch-<version>.nvda-addon`, together with a
`.nvda-addon.sha256` checksum file. The version comes from `buildVars.py`.
No fixed-name latest-download asset is generated.

The default build generates HTML help, compiles PO to MO, creates the English
and localized manifests, copies license notices and packages the add-on.
Generated files remain local and are ignored by Git. The package excludes
Markdown and gettext source files, Python bytecode and caches.

`uv run --locked scons -c` removes generated build targets. Source manuals
are retained. If you only want a package, `uv run --locked scons` is sufficient
after installing the prerequisites. Run the validation commands before sharing it.

## Source files and generated files

| Source | Generated output |
| --- | --- |
| `buildVars.py` and `manifest.ini.tpl` | `addon/manifest.ini` |
| `addon/locale/<lang>/LC_MESSAGES/nvda.po` | `nvda.mo` and localized `manifest.ini` |
| `addon/doc/<lang>/readme.md` | `addon/doc/<lang>/readme.html` |
| `style.css` | `addon/doc/style.css` |
| `COPYING.txt`, `THIRD_PARTY_NOTICES.md` | License notices in the package |
| Python sources and `buildVars.py` | `addon/locale/nvda.pot`, when running `scons pot` |

`README.md`, `README.pl.md` and `README.sk.md` are repository overviews.
They do not overwrite the full manuals. Edit the Markdown and PO sources,
not the generated HTML, MO or manifest files.

The build tracks source code, help, translations, DLLs and notices so that
changes to these inputs rebuild the relevant output. `buildVars.py` is the
source of add-on identity, version, description, compatibility and package rules.

## Repository structure

- `addon/globalPlugins/globalSonicPitch/`: modular global plugin; `__init__.py`
  retains the NVDA entry point. See the module map in [technical notes](technical-notes.md).
- `addon/sapi32HostDrivers/`: existing SAPI4/SAPI5 host wrappers.
- `addon/globalPlugins/sonicPitchNative/`: unchanged native DLLs and their provenance.
- `addon/doc/`: full user manuals in English, Polish and Slovak.
- `addon/locale/`: gettext template and translated PO catalogs.
- `site_scons/`, `sconstruct`, manifest templates: build infrastructure.
- `tools/check_project.py`: source, translation and package validation.
- `docs/`: build, translation, technical and release guidance.
- `docs/archive/`: historical observations, not a current compatibility promise.

## Template provenance and adaptations

Build infrastructure is based on
[NV Access AddonTemplate revision 56f272d5e37711949b9baf069194455f0386f152](https://github.com/nvaccess/AddonTemplate/tree/56f272d5e37711949b9baf069194455f0386f152).
The template's `site_scons` tools and license text are included. The gettext
tool enables `msgfmt --check --check-format`. A small project stylesheet keeps
text left-aligned and provides readable tables and visible keyboard focus.

The project-specific `sconstruct` keeps manuals separate from the root README,
keeps the existing POT path, tracks native assets and copies license notices.
Its clean rule removes generated targets rather than the source manual directory.
The manifest templates retain the existing NVDA metadata fields; optional empty
changelog and update-channel fields are omitted. Crowdin synchronization and
the template's automatic release-publishing workflow are not enabled.

## GitHub Actions

The workflow builds on Ubuntu with Python 3.13 after a push, pull request or
manual invocation. It validates translations, runs the NVDA-double regression
tests with `uv run --locked python -m unittest discover -s tests -v`, builds the package and uploads
the package, checksum and generated POT as review artifacts. It has read-only
repository permissions and does not create releases or update the Add-on Store.
Actions are pinned to commit revisions; dependency updates should be reviewed.

A successful workflow confirms build and package checks. It does not run
NVDA or validate speech playback. Use [TESTING.md](../TESTING.md) for runtime checks
and [release guidance](addon-store-submission.md) when preparing a future release.
