# Contributing

Report bugs through [GitHub Issues](https://github.com/djgraco/sonicpitch/issues)
with reproduction steps, NVDA version and architecture, synthesizer and voice,
add-on version and relevant settings. Include reviewed diagnostic log entries
when available.

For code or documentation changes, work on a separate branch and keep each
change focused. Follow [building instructions](docs/building.md), run the
source and package checks, and describe the results in the pull request.
Translation instructions are in [docs/translating.md](docs/translating.md).

Do not edit generated HTML, MO or manifest files. Update their sources instead.
Keep interface labels and the English, Polish and Slovak manuals consistent.
Record user-visible changes under **Unreleased** in [CHANGELOG.md](CHANGELOG.md).

Speech processing depends on NVDA internals and native stream lifetime rules.
Read [technical notes](docs/technical-notes.md) and the regression history before
changing this code. Preserve safe speech boundaries, locking, stream retirement,
dialog rollback and hook cleanup unless a separately tested change replaces them.
Do not remove a workaround solely because its purpose is not immediately obvious.

For runtime changes, report actual Windows/NVDA tests from [TESTING.md](TESTING.md).
Do not describe static checks as playback tests or increase NVDA compatibility
metadata without testing that NVDA version.
