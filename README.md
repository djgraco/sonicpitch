# Global Sonic Pitch

Global Sonic Pitch lets you lower or raise the pitch of NVDA speech using the
Sonic audio library. It adds a separate **Sonic pitch** control, independent of
the synthesizer's own **Pitch** setting, so you can adjust the sound of a voice
without changing the configured speech rate.

English | [Polski](README.pl.md) | [Slovenčina](README.sk.md)

## Features

- Adjust speech pitch from NVDA's Voice settings or synth settings ring.
- Keep separate values for synthesizers, voices and supported voice variants.
- Choose the standard range of −6 to +6 semitones or an extended range of
  −20 to +20 semitones. The neutral value is 50 in both ranges.
- Optionally enable higher-quality Sonic processing.
- Assign your own gestures to toggle processing, change pitch or reset it.

The add-on works with supported NVDA speech output, including eSpeak NG,
OneCore, RHVoice and supported SAPI configurations. Compatibility depends on
how the synthesizer sends audio to NVDA; see the [user guide](addon/doc/en/readme.md).

## Installation and first use

Install **Global Sonic Pitch** from NVDA's Add-on Store, or download
`globalSonicPitch-<version>.nvda-addon` from [Releases](https://github.com/djgraco/sonicpitch/releases).
For a downloaded file, use NVDA's option to install an add-on from a file.
Restart NVDA when prompted.

1. Open NVDA Settings and select **Global Sonic Pitch**.
2. Select **Enable global Sonic pitch**, then choose **OK** or **Apply**.
3. Open **Voice** settings and adjust **Sonic pitch**. Values below 50 lower
   the voice; values above 50 raise it.

Processing is disabled by default. You continue to use your existing
synthesizer; no additional synthesizer needs to be selected.

## Documentation and development

- [User guide](addon/doc/en/readme.md)
- [Release history](CHANGELOG.md)
- [Build and repository structure](docs/building.md)
- [Translation guide](docs/translating.md)
- [Technical notes](docs/technical-notes.md)
- [Testing checklist](TESTING.md)
- [Contributing](CONTRIBUTING.md)

To build from source, install the prerequisites described in the build guide,
then run `uv sync --locked` and `uv run scons`. The build generates HTML help,
compiled translations and manifests before creating the versioned add-on package.
The build tools are based on the [NVDA Add-on Template](https://github.com/nvaccess/AddonTemplate).

## License

The add-on source is licensed under the GNU GPL, version 2 or later. See
[LICENSE.md](LICENSE.md) and [COPYING.txt](COPYING.txt). Bundled Sonic DLLs are
Apache 2.0 components; see [third-party notices](THIRD_PARTY_NOTICES.md).
