# Translating Global Sonic Pitch

Translations are maintained in this repository. This maintenance setup does
not introduce automatic synchronization with Crowdin.

## Interface and manifest

1. Set up the build tools described in [building.md](building.md).
2. Run `uv run --locked scons pot` from the repository root.
3. Update `addon/locale/<lang>/LC_MESSAGES/nvda.po` from
   `nvda.pot` in the repository root, using Poedit or `msgmerge`.
4. Translate new entries and review changed or fuzzy entries.
5. Run `uv run --locked python tools/check_project.py`.
6. Build with `uv run --locked scons` and validate the resulting package with
   `uv run --locked python tools/check_project.py --package`.

The manifest summary and description are gettext messages in `buildVars.py`.
Their translations belong in the same PO file as the interface. The build
creates MO files and localized manifests automatically. Keep the product
name **Global Sonic Pitch** unchanged. **Sonic pitch** is retained as the
existing setting label in the Polish and Slovak interface.

Preserve placeholders such as `{synth}`, `{pitch}`, `{url}` and `{reason}`.
Read the translator comments and check where a message is used. For Polish,
Input Gestures descriptions describe actions in the third person, for example
“Zwiększa”, while button and menu labels may use commands such as “Otwórz”.

## User documentation

The full English manual is `addon/doc/en/readme.md`. Translate its structure
and meaning into `addon/doc/<lang>/readme.md`; HTML is generated during the build.
Use the exact translated labels from the PO catalog when naming add-on controls.
Keep useful compatibility limitations and the explanation of the neutral value
and pitch ranges. Avoid moving implementation details into basic setup steps.

The root `README.<lang>.md` is a short overview with installation steps and
links. It should not duplicate the full manual or release history. If a feature
changes, update the English, Polish and Slovak overviews and manuals together.

Before submitting, open the generated help from NVDA, check heading and table
navigation with a screen reader, and confirm that its labels match the actual
interface. A build check cannot assess the naturalness of a translation.
