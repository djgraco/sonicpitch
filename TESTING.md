# Testing Global Sonic Pitch

Build checks and NVDA runtime tests cover different things. Record the actual
environments and results; an unchecked item is not a claim of compatibility.

## Automated build checks

From the repository root, run:

1. `uv sync --locked`
2. `uv run --locked scons pot`
3. `uv run --locked python tools/check_project.py`
4. `uv run --locked scons`
5. `uv run --locked python tools/check_project.py --package --write-checksum`

The checks cover Python syntax, source/POT/PO consistency, translated
placeholders, compiled catalogs, generated manifest descriptions, package paths,
required DLLs and licenses, and basic HTML heading/table structure.

Check build integration after changing build tools:

- Build from a clean checkout without pre-generated HTML, MO or manifests.
- Change a manual and confirm its HTML and the package rebuild.
- Change a PO entry and confirm the MO and translated manifest rebuild.
- Confirm a native asset or notice change rebuilds the package.
- Run `uv run --locked scons -c` and confirm source manuals remain intact.
- Rebuild and validate the package again.

## Windows and NVDA runtime matrix

Test the minimum declared NVDA version and the latest declared tested version,
using the relevant 32-bit and 64-bit NVDA builds. Add future compatibility
versions only after actual testing.

Record at least the NVDA version and architecture, Windows version,
synthesizer and voice, add-on package checksum, settings and observed result.

Speech paths to cover:

- eSpeak NG, OneCore and RHVoice through NVDA's main audio output.
- SAPI5 in the main process, including an affected third-party SAPI voice if available.
- Standard `sapi5_32` on 64-bit NVDA.
- Standard `sapi4_32` on 64-bit NVDA with WASAPI enabled.
- The older SAPI4 audio path: confirm the documented unsupported behavior.

## Basic behavior

- A fresh configuration has processing, extended range and higher quality disabled.
- The settings panel appears. No replacement synthesizer entries are added.
- Sonic pitch appears in Voice settings and the synth settings ring only when enabled.
- 50 is neutral; smaller values lower the voice and larger values raise it.
- The native Pitch control remains independent.
- Standard and extended ranges have the documented effect; changing the range
  changes the effect of saved non-neutral values.
- Higher-quality mode preserves pitch mapping and speech remains audible.
- Distinct synthesizers, voices and supported variants retain their values.
- Returning to a voice or variant restores the expected value.
- Saving and restarting NVDA restores the expected settings.
- Changes in Voice settings can be previewed; OK/Apply saves them and Cancel/Escape
  discards changes since the last save, including changes across voice variants.
- Ring and assigned-gesture changes are saved immediately.
- All six Input Gestures commands appear; none is assigned by default.
- Non-speech NVDA sounds and audio from other applications remain unaffected.

## Regression checks

Preserve the cases behind the changelog, especially:

- Rapid PageUp/PageDown changes while speaking, including downward changes
  with SAPI voices at high rate.
- Both quality modes and both pitch ranges on affected host paths.
- Interrupting speech, short first audio blocks, continuous reading and say-all.
- Switching away from `sapi5_32` and back restores its saved per-voice value.
- Repeatedly opening, saving, cancelling and reopening Voice settings after
  SAPI4/SAPI5 switches.
- Switching only a voice variant refreshes the visible control and preserves
  independent pending/saved values.
- Dynamic voice settings, including Google TTS if installed, retain their
  original behavior alongside Sonic pitch.
- soundWave rendering while it temporarily replaces `nvwave.WavePlayer`.
- Disable/unload/reload behavior restores runtime hooks and leaves speech working.
- No freeze, unexpected silence, access violation or Global Sonic Pitch traceback.

These tests are needed for runtime refactoring as well as NVDA compatibility changes.

## Localization and help

- English, Polish and Slovak help opens from NVDA.
- Heading and table navigation works with a screen reader.
- Labels in the manuals match the actual translated controls.
- Manifest descriptions explain the purpose of the add-on.
- Polish Input Gestures descriptions describe the command's action.
- Support controls open the intended page only after activation.
- The installation/update support prompt permits continuing without support.

## Reporting failures

Use the add-on's debug logging and collect relevant NVDA or 32-bit host log
entries. Include reproduction steps and actual environment details. Review
logs for private text before sharing.

See [technical notes](docs/technical-notes.md) for implementation details and
[release guidance](docs/addon-store-submission.md) before publishing a package.
