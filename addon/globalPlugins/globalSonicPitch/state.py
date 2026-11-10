"""One shared instance of configuration constants and runtime state."""

from __future__ import annotations

from ._nvda import (
	Any,
	Callable,
	threading,
	weakref,
)


CONFIG_SECTION = "globalSonicPitch"
OLD_CONFIG_SECTION = "sapi5SonicPitchGlobal"
CONFIG_SPEC = {
	"enabled": "boolean(default=False)",
	"pitch": "integer(default=50, min=0, max=100)",
	"pitchBySynth": "string(default='{}')",
	"extendedPitchRange": "boolean(default=False)",
	"sonicQuality": "integer(default=0, min=0, max=1)",
	"debugLogging": "boolean(default=False)",
}
NEUTRAL_PITCH = 50
STANDARD_MAX_SEMITONES = 6.0
EXTENDED_MAX_SEMITONES = 20.0
SONIC_PITCH_SETTING_ID = "sonicPitch"
SONIC_PITCH_EXTENDED_RANGE_PARAM_ID = "_sonicPitchExtendedRange"
SONIC_QUALITY_PARAM_ID = "_sonicQuality"
SONIC_PITCH_HOST_SETTING_IDS = {SONIC_PITCH_SETTING_ID, SONIC_PITCH_EXTENDED_RANGE_PARAM_ID, SONIC_QUALITY_PARAM_ID}
SUPPORT_URL = "https://buycoffee.to/kazimierz-parzych"
LEGACY_PITCH_CONFIG_KEY = "pitch"
PITCH_BY_SYNTH_CONFIG_KEY = "pitchBySynth"
EXTENDED_PITCH_RANGE_CONFIG_KEY = "extendedPitchRange"
SONIC_QUALITY_CONFIG_KEY = "sonicQuality"
VOICE_KEY_SEPARATOR = "::voice::"
VARIANT_KEY_SEPARATOR = "::variant::"
_ORIGINAL_FEED_ATTR = "_globalSonicPitchOriginalFeed"
_ORIGINAL_IDLE_ATTR = "_globalSonicPitchOriginalIdle"
_ORIGINAL_STOP_ATTR = "_globalSonicPitchOriginalStop"
_ORIGINAL_CLOSE_ATTR = "_globalSonicPitchOriginalClose"
_FEED_PATCHED_ATTR = "_globalSonicPitchFeedPatched"
_ORIGINAL_SET_SYNTH_ATTR = "_globalSonicPitchOriginalSetSynth"
_SET_SYNTH_PATCHED_ATTR = "_globalSonicPitchSetSynthPatched"
_SET_SYNTH_WRAPPER_ATTR = "_globalSonicPitchSetSynthWrapper"
_ORIGINAL_SETTINGS_SET_SYNTH_ATTR = "_globalSonicPitchOriginalSettingsSetSynth"
_SETTINGS_SET_SYNTH_PATCHED_ATTR = "_globalSonicPitchSettingsSetSynthPatched"
_SETTINGS_SET_SYNTH_WRAPPER_ATTR = "_globalSonicPitchSettingsSetSynthWrapper"
_ORIGINAL_AUTO_SETTINGS_REFRESH_GUI_ATTR = "_globalSonicPitchOriginalAutoSettingsRefreshGui"
_AUTO_SETTINGS_REFRESH_GUI_PATCHED_ATTR = "_globalSonicPitchAutoSettingsRefreshGuiPatched"
_AUTO_SETTINGS_REFRESH_GUI_WRAPPER_ATTR = "_globalSonicPitchAutoSettingsRefreshGuiWrapper"
_ORIGINAL_SETTINGS_DIALOG_DESTROYED_STATE_ATTR = "_globalSonicPitchOriginalSettingsDialogDestroyedState"
_SETTINGS_DIALOG_DESTROYED_STATE_PATCHED_ATTR = "_globalSonicPitchSettingsDialogDestroyedStatePatched"
_SETTINGS_DIALOG_DESTROYED_STATE_WRAPPER_ATTR = "_globalSonicPitchSettingsDialogDestroyedStateWrapper"
_ORIGINAL_VOICE_PANEL_MAKE_SETTINGS_ATTR = "_globalSonicPitchOriginalVoicePanelMakeSettings"
_ORIGINAL_VOICE_PANEL_ON_SAVE_ATTR = "_globalSonicPitchOriginalVoicePanelOnSave"
_ORIGINAL_VOICE_PANEL_ON_DISCARD_ATTR = "_globalSonicPitchOriginalVoicePanelOnDiscard"
_VOICE_PANEL_PATCHED_ATTR = "_globalSonicPitchVoicePanelPatched"
_ORIGINAL_SUPPORTED_SETTINGS_ATTR = "_globalSonicPitchOriginalSupportedSettings"
_SONIC_PITCH_SETTING_PATCHED_ATTR = "_globalSonicPitchVoiceSettingPatched"
_BUNDLED_SONIC_DIR = "sonicPitchNative"
_BUNDLED_SONIC_32_DLL = "sonic32.dll"
_BUNDLED_SONIC_64_DLL = "sonic64.dll"
_SAPI32_HOST_DRIVER_DIR = "sapi32HostDrivers"
_ORIGINAL_SAPI32_HOST_PATH_ATTR = "_globalSonicPitchOriginalSynthDriver32Path"
_SAPI32_HOST_PATH_PATCHED_ATTR = "_globalSonicPitchHostPathPatched"
_sonicModule = None
_processingLogKeys: set[tuple[Any, ...]] = set()
_deferredPitchLogKeys: set[tuple[Any, ...]] = set()
_voiceSettingLogKeys: set[str] = set()
_sonicUnavailableReason: str | None = None
_sonicPitchDriverSetting: Any | None = None
_missingClassAttr = object()
_sonicPitchClassPatches: dict[type, Any] = {}
_supportedSettingsClassPatches: dict[type, Any] = {}
_voiceClassPatches: dict[type, Any] = {}
_variantClassPatches: dict[type, Any] = {}
_originalWavePlayerClass: Any | None = None
_originalWavePlayerMethods: dict[str, Callable[..., Any]] = {}
_configMigrated = False
_deferSynthPitchPatchDepth = 0
_noDestroySonicStreamLogged = False
_playerProcessors: dict[int, "_SonicStreamProcessor"] = {}
_playerUtterancePitches: dict[int, int] = {}
_playerUtteranceQualities: dict[int, int] = {}
_playerProcessorsLock = threading.RLock()
_FIRST_AUDIO_CHUNK_MIN_DURATION_MS = 50
_SHORT_AUDIO_CHUNK_MAX_DURATION_MS = 35
_sapi32HostReloading = False
_sapi32HostReloadRequested = False
_voiceDialogSessions: dict[int, dict[str, dict[str, int]]] = {}
_voiceDialogPanelRefs: dict[int, weakref.ReferenceType[Any]] = {}
_voiceDialogSonicPitchRefreshPending = False
_settingsDialogGcPending = False
_runtimeSonicPitchByKey: dict[str, tuple[int, bool, int]] = {}
_qualityLogKeys: set[tuple[Any, ...]] = set()
_synthSwitchDiagnosticSequence = 0
_lastSynthSwitchStartedAt: float | None = None
_lastSynthSwitchCompletedAt: float | None = None
_lastSynthSwitchSource = ""
_lastSynthSwitchRequestedSynth = ""
_lastSynthSwitchBeforeSynth = ""
_lastSynthSwitchAfterSynth = ""
_lastSynthSwitchFailed = False
