"""Configuration, pitch mapping and per-voice value storage."""

from __future__ import annotations

from ._nvda import (
	Any,
	config,
	json,
	log,
)
from . import audio as _audio
from . import dialogs as _dialogs
from . import host as _host
from . import state as _state
from . import synths as _synths


def _ensureConfigSpec() -> None:
	config.conf.spec[_state.CONFIG_SECTION] = _state.CONFIG_SPEC
	if not _state._configMigrated:
		_migrateOldConfigSection()
		_state._configMigrated = True


def _migrateOldConfigSection() -> None:
	try:
		if _state.OLD_CONFIG_SECTION not in config.conf:
			return
		oldConf = config.conf[_state.OLD_CONFIG_SECTION]
		newConf = config.conf[_state.CONFIG_SECTION]
	except Exception:
		return
	for key in ("enabled", "pitch", "debugLogging"):
		try:
			if key in oldConf:
				newConf[key] = oldConf[key]
		except Exception:
			continue


def _getConfigValue(key: str, default: Any) -> Any:
	try:
		_ensureConfigSpec()
		return config.conf[_state.CONFIG_SECTION].get(key, default)
	except Exception:
		return default


def _setConfigValue(key: str, value: Any) -> None:
	_ensureConfigSpec()
	config.conf[_state.CONFIG_SECTION][key] = value


def _setGlobalEnabled(enabled: bool) -> None:
	if enabled:
		_host._installSapi32HostDriverPatch()
	_setConfigValue("enabled", bool(enabled))
	_audio._resetAllPlayerProcessors()
	_synths._patchCurrentSynthPitch()


def _isExtendedPitchRangeEnabled() -> bool:
	return bool(_getConfigValue(_state.EXTENDED_PITCH_RANGE_CONFIG_KEY, False))


def _setExtendedPitchRangeEnabled(enabled: bool) -> None:
	enabled = bool(enabled)
	wasEnabled = _isExtendedPitchRangeEnabled()
	_setConfigValue(_state.EXTENDED_PITCH_RANGE_CONFIG_KEY, enabled)
	if wasEnabled == enabled:
		return
	_audio._resetAllPlayerProcessors()
	_state._runtimeSonicPitchByKey.clear()
	_synths._patchCurrentSynthPitch()


def _clamp(value: float, minimum: float, maximum: float) -> float:
	return max(minimum, min(maximum, value))


def _clampPitch(value: int | float) -> int:
	try:
		numericValue = float(value)
	except Exception:
		numericValue = float(_state.NEUTRAL_PITCH)
	return int(_clamp(numericValue, 0.0, 100.0))


def _clampQuality(value: Any) -> int:
	try:
		return 1 if int(value) == 1 else 0
	except Exception:
		return 0


def _getSonicQuality() -> int:
	return _clampQuality(_getConfigValue(_state.SONIC_QUALITY_CONFIG_KEY, 0))


def _setSonicQuality(value: Any) -> None:
	quality = _clampQuality(value)
	oldQuality = _getSonicQuality()
	_setConfigValue(_state.SONIC_QUALITY_CONFIG_KEY, quality)
	if oldQuality == quality:
		return
	_audio._resetAllPlayerProcessors()
	_state._runtimeSonicPitchByKey.clear()
	_synths._patchCurrentSynthPitch()
	log.info(f"globalSonicPitch: Sonic processing quality set to {quality} ({_getQualityLabel(quality)})")


def _getQualityLabel(quality: int) -> str:
	return "higher quality" if _clampQuality(quality) == 1 else "fast"


def _pitchPercentToSonicRatio(pitchPercent: int | float) -> float:
	pitchPercent = _clamp(float(pitchPercent), 0.0, 100.0)
	maxSemitones = _state.EXTENDED_MAX_SEMITONES if _isExtendedPitchRangeEnabled() else _state.STANDARD_MAX_SEMITONES
	semitones = ((pitchPercent - 50.0) / 50.0) * maxSemitones
	ratio = 2.0 ** (semitones / 12.0)
	minRatio = 2.0 ** (-maxSemitones / 12.0)
	maxRatio = 2.0 ** (maxSemitones / 12.0)
	return _clamp(ratio, minRatio, maxRatio)


def _isDebugLoggingEnabled() -> bool:
	return bool(_getConfigValue("debugLogging", False))


def _loadSynthPitchMap() -> dict[str, int]:
	value = _getConfigValue(_state.PITCH_BY_SYNTH_CONFIG_KEY, "{}")
	if isinstance(value, dict):
		data = value
	else:
		try:
			data = json.loads(str(value or "{}"))
		except Exception:
			if _isDebugLoggingEnabled():
				log.debugWarning("globalSonicPitch: failed to parse per-synth pitch config", exc_info=True)
			return {}
	if not isinstance(data, dict):
		return {}
	pitches: dict[str, int] = {}
	for synthName, pitch in data.items():
		key = _synths._normalizePitchStorageKey(str(synthName))
		if key:
			pitches[key] = _clampPitch(pitch)
	return pitches


def _saveSynthPitchMap(pitches: dict[str, int]) -> None:
	serializable = {
		_synths._normalizePitchStorageKey(synthName): _clampPitch(pitch)
		for synthName, pitch in pitches.items()
		if _synths._normalizePitchStorageKey(synthName)
	}
	_setConfigValue(
		_state.PITCH_BY_SYNTH_CONFIG_KEY,
		json.dumps(serializable, sort_keys=True, separators=(",", ":")),
	)


def _getStoredSonicPitchForKey(key: str | None) -> int:
	key = _synths._normalizePitchStorageKey(key)
	if not key:
		return _state.NEUTRAL_PITCH
	pitches = _loadSynthPitchMap()
	if key in pitches:
		return pitches[key]
	variantlessKey = _synths._getVariantlessPitchStorageKey(key)
	if variantlessKey != key and variantlessKey in pitches:
		return pitches[variantlessKey]
	baseKey = _synths._getBasePitchKeyFromStorageKey(key)
	if key != baseKey and baseKey in pitches:
		pitch = pitches.pop(baseKey)
		pitches[key] = pitch
		_saveSynthPitchMap(pitches)
		log.info(
			"globalSonicPitch: migrated per-synth Sonic pitch to current voice; "
			f"synth={baseKey}; key={key}; sonicPitch={pitch}",
		)
		return pitch
	return _state.NEUTRAL_PITCH


def _migrateLegacyGlobalPitchToKey(key: str) -> None:
	legacyPitch = _clampPitch(_getConfigValue(_state.LEGACY_PITCH_CONFIG_KEY, _state.NEUTRAL_PITCH))
	if legacyPitch == _state.NEUTRAL_PITCH:
		return
	key = _synths._normalizePitchStorageKey(key)
	baseKey = _synths._getBasePitchKeyFromStorageKey(key)
	if not key or not _synths._isGlobalAudioSupportedSynth(baseKey):
		return
	pitches = _loadSynthPitchMap()
	if not pitches:
		pitches[key] = legacyPitch
		_saveSynthPitchMap(pitches)
		log.info(
			"globalSonicPitch: migrated global Sonic pitch to current synth; "
			f"key={key}; sonicPitch={legacyPitch}",
		)
	_setConfigValue(_state.LEGACY_PITCH_CONFIG_KEY, _state.NEUTRAL_PITCH)


def _setSonicPitchForKey(key: str | None, pitch: int | float) -> int | None:
	key = _synths._normalizePitchStorageKey(key)
	baseKey = _synths._getBasePitchKeyFromStorageKey(key)
	if not key or not _synths._isGlobalAudioSupportedSynth(baseKey):
		return None
	pitch = _clampPitch(pitch)
	pitches = _loadSynthPitchMap()
	oldPitch = pitches.get(key, _state.NEUTRAL_PITCH)
	pitches[key] = pitch
	_saveSynthPitchMap(pitches)
	_setConfigValue(_state.LEGACY_PITCH_CONFIG_KEY, _state.NEUTRAL_PITCH)
	if pitch != oldPitch:
		_audio._clearIdlePlayerUtterancePitches()
		log.info(
			"globalSonicPitch: stored Sonic pitch for next safe audio boundary; "
			f"key={key}; oldPitch={oldPitch}; pendingPitch={pitch}",
		)
	return pitch


def _getSonicPitchForSynth(synthOrName: Any | None = None) -> int:
	key = _synths._getSonicPitchStorageKey(synthOrName)
	if not key:
		return _state.NEUTRAL_PITCH
	pendingPitch = _dialogs._getVoiceDialogPendingPitch(key)
	if pendingPitch is not None:
		return pendingPitch
	_migrateLegacyGlobalPitchToKey(key)
	return _getStoredSonicPitchForKey(key)


def _setSonicPitchForSynth(synthOrName: Any | None, pitch: int | float) -> int | None:
	return _setSonicPitchForKey(_synths._getSonicPitchStorageKey(synthOrName), pitch)


def _setCurrentSynthSonicPitch(pitch: int | float) -> int | None:
	synth = _synths._getCurrentSynth()
	if _dialogs._setVoiceDialogPendingSonicPitch(synth, pitch):
		return _clampPitch(pitch)
	pitch = _setSonicPitchForSynth(synth, pitch)
	if pitch is not None:
		_host._applyRuntimeSonicPitch(synth, pitch)
	return pitch


def _changeCurrentSynthSonicPitch(delta: int) -> int | None:
	return _setCurrentSynthSonicPitch(_getSonicPitchForSynth(_synths._getCurrentSynth()) + delta)
