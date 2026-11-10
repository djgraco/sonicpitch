"""Synthesizer identity, dynamic voice settings and synth-switch hooks."""

from __future__ import annotations

from ._nvda import (
	Any,
	Callable,
	NumericDriverSetting,
	config,
	functools,
	globalVars,
	inspect,
	log,
	settingsDialogs,
	synthDriverHandler,
	wx,
)
from ._nvda import gettext as _
from . import audio as _audio
from . import configuration as _configuration
from . import dialogs as _dialogs
from . import host as _host
from . import native as _native
from . import state as _state


def _getCurrentSynth() -> Any | None:
	if synthDriverHandler is None:
		return None
	try:
		return synthDriverHandler.getSynth()
	except Exception:
		return None


def _getSynthName(synth: Any | None = None) -> str:
	if synth is None:
		synth = _getCurrentSynth()
	return str(getattr(synth, "name", "") or "")


def _getCurrentSynthDisplayName() -> str:
	# Translators: Fallback synthesizer name used in spoken status messages.
	return _getSynthName() or _("current synth")


def _isGlobalAudioSupportedSynth(synthName: str) -> bool:
	if synthName.startswith("sapi5SonicPitch"):
		return False
	return True


def _getSynthPitchKey(synthName: str | None) -> str:
	key = str(synthName or "").strip()
	if key == "sapi5":
		return "sapi5_32" if _native._is32BitProcess() else "sapi5_64"
	if key == "sapi5_32":
		return "sapi5_32"
	return key


def _normalizePitchStorageKey(key: str | None) -> str:
	key = str(key or "").strip()
	if not key:
		return ""
	synthName, separator, voiceId = key.partition(_state.VOICE_KEY_SEPARATOR)
	synthKey = _getSynthPitchKey(synthName)
	if not separator:
		return synthKey
	voiceId = str(voiceId or "").strip()
	if not synthKey or not voiceId:
		return synthKey
	return f"{synthKey}{_state.VOICE_KEY_SEPARATOR}{voiceId}"


def _getBasePitchKeyFromStorageKey(key: str | None) -> str:
	key = _normalizePitchStorageKey(key)
	synthName, _, _voiceId = key.partition(_state.VOICE_KEY_SEPARATOR)
	return _getSynthPitchKey(synthName)


def _getVariantlessPitchStorageKey(key: str | None) -> str:
	key = _normalizePitchStorageKey(key)
	synthName, separator, voiceId = key.partition(_state.VOICE_KEY_SEPARATOR)
	if not separator:
		return key
	voiceId, variantSeparator, _variantId = voiceId.partition(_state.VARIANT_KEY_SEPARATOR)
	if not variantSeparator:
		return key
	synthKey = _getSynthPitchKey(synthName)
	voiceId = str(voiceId or "").strip()
	if not synthKey or not voiceId:
		return synthKey
	return f"{synthKey}{_state.VOICE_KEY_SEPARATOR}{voiceId}"


def _stringifyVoiceIdentifier(value: Any) -> str:
	if value is None:
		return ""
	if isinstance(value, bytes):
		try:
			value = value.decode("utf-8", errors="replace")
		except Exception:
			value = repr(value)
	if not isinstance(value, str):
		for attr in ("id", "ID", "name", "displayName"):
			try:
				attrValue = getattr(value, attr, None)
			except Exception:
				attrValue = None
			if attrValue:
				return str(attrValue).strip()
	return str(value).strip()


def _getSynthVoiceId(synth: Any | None) -> str:
	if synth is None:
		return ""
	for attr in ("voice", "_voice"):
		try:
			voiceId = _stringifyVoiceIdentifier(getattr(synth, attr))
		except Exception:
			continue
		if voiceId and voiceId.lower() != "none":
			return voiceId
	return ""


def _getSynthVariantId(synth: Any | None) -> str:
	if synth is None:
		return ""
	for attr in ("variant", "_variant"):
		try:
			variantId = _stringifyVoiceIdentifier(getattr(synth, attr))
		except Exception:
			continue
		if variantId and variantId.lower() != "none":
			return variantId
	return ""


def _getSynthVoiceIdentity(synth: Any | None) -> str:
	voiceId = _getSynthVoiceId(synth)
	if not voiceId:
		return ""
	variantId = _getSynthVariantId(synth)
	if variantId and variantId != voiceId:
		return f"{voiceId}{_state.VARIANT_KEY_SEPARATOR}{variantId}"
	return voiceId


def _getSonicPitchStorageKey(synthOrName: Any | None = None) -> str:
	if synthOrName is None:
		synthOrName = _getCurrentSynth()
	if isinstance(synthOrName, str):
		return _normalizePitchStorageKey(synthOrName)
	synthKey = _getSynthPitchKey(_getSynthName(synthOrName))
	if not synthKey:
		return ""
	voiceId = _getSynthVoiceIdentity(synthOrName)
	if not voiceId:
		return synthKey
	return _normalizePitchStorageKey(f"{synthKey}{_state.VOICE_KEY_SEPARATOR}{voiceId}")


def _isRemoteSapi32Synth(synthName: str | None) -> bool:
	return not _native._is32BitProcess() and str(synthName or "").strip() in {"sapi4_32", "sapi5_32"}


def _getSonicPitchDriverSetting() -> Any | None:
	if NumericDriverSetting is None:
		return None
	if _state._sonicPitchDriverSetting is not None:
		return _state._sonicPitchDriverSetting
	try:
		_state._sonicPitchDriverSetting = NumericDriverSetting(
			_state.SONIC_PITCH_SETTING_ID,
			# Translators: Name of the add-on pitch setting in NVDA Voice settings.
			_("Sonic pitch"),
			availableInSettingsRing=True,
			defaultVal=_state.NEUTRAL_PITCH,
			minVal=0,
			maxVal=100,
			minStep=1,
			normalStep=5,
			largeStep=10,
			# Translators: Display name of the add-on pitch setting in the synth settings ring.
			displayName=_("Sonic pitch"),
			useConfig=False,
		)
	except TypeError:
		try:
			_state._sonicPitchDriverSetting = NumericDriverSetting(
				_state.SONIC_PITCH_SETTING_ID,
				# Translators: Name of the add-on pitch setting in NVDA Voice settings.
				_("Sonic pitch"),
				True,
				_state.NEUTRAL_PITCH,
				0,
				100,
				1,
				5,
				10,
				# Translators: Display name of the add-on pitch setting in the synth settings ring.
				_("Sonic pitch"),
				False,
			)
		except Exception:
			log.debugWarning("globalSonicPitch: failed to create Sonic pitch voice setting", exc_info=True)
			return None
	except Exception:
		log.debugWarning("globalSonicPitch: failed to create Sonic pitch voice setting", exc_info=True)
		return None
	return _state._sonicPitchDriverSetting


def _settingId(setting: Any) -> str:
	return str(getattr(setting, "id", "") or "")


def _hasSonicPitchSetting(settings: Any) -> bool:
	try:
		return any(_settingId(setting) == _state.SONIC_PITCH_SETTING_ID for setting in settings)
	except Exception:
		return False


def _withoutSonicPitchSettings(settings: Any) -> tuple[Any, ...]:
	try:
		return tuple(setting for setting in settings if _settingId(setting) not in _state.SONIC_PITCH_HOST_SETTING_IDS)
	except Exception:
		try:
			return tuple(settings or ())
		except Exception:
			return ()


def _withSonicPitchSetting(settings: Any, setting: Any | None = None) -> tuple[Any, ...]:
	filteredSettings = _withoutSonicPitchSettings(settings)
	if setting is None:
		setting = _getSonicPitchDriverSetting()
	if setting is None:
		return filteredSettings
	return filteredSettings + (setting,)


def _findInheritedSupportedSettingsDescriptor(synthClass: type) -> Any:
	for baseClass in getattr(synthClass, "__mro__", ())[1:]:
		try:
			namespace = getattr(baseClass, "__dict__", {})
		except Exception:
			continue
		if "supportedSettings" in namespace:
			return namespace["supportedSettings"]
	return _state._missingClassAttr


def _isDataDescriptor(value: Any) -> bool:
	return value is not _state._missingClassAttr and (
		hasattr(value, "__set__") or hasattr(value, "__delete__")
	)


def _isDynamicSupportedSettingsDescriptor(value: Any) -> bool:
	if value is _state._missingClassAttr:
		return False
	if isinstance(value, property):
		return True
	return hasattr(value, "__get__") or _isDataDescriptor(value)


def _supportedSettingsDescriptorForClass(synthClass: type) -> Any:
	try:
		value = synthClass.__dict__.get("supportedSettings", _state._missingClassAttr)
	except Exception:
		value = _state._missingClassAttr
	if value is not _state._missingClassAttr:
		return value
	return _findInheritedSupportedSettingsDescriptor(synthClass)


def _getOriginalSupportedSettings(instance: Any, synthClass: type, originalValue: Any) -> Any:
	value = originalValue
	if value is _state._missingClassAttr:
		value = _findInheritedSupportedSettingsDescriptor(synthClass)
	if instance is not None and not _isDataDescriptor(value):
		try:
			instanceSettings = getattr(instance, "__dict__", {}).get("supportedSettings", _state._missingClassAttr)
		except Exception:
			instanceSettings = _state._missingClassAttr
		if instanceSettings is not _state._missingClassAttr:
			return instanceSettings
	if value is _state._missingClassAttr:
		return ()
	if hasattr(value, "__get__"):
		return value.__get__(instance, synthClass)
	return value


def _setOriginalSupportedSettings(instance: Any, synthClass: type, originalValue: Any, settings: Any) -> None:
	value = originalValue
	if value is _state._missingClassAttr:
		value = _findInheritedSupportedSettingsDescriptor(synthClass)
	filteredSettings = _withoutSonicPitchSettings(settings)
	if value is not _state._missingClassAttr and hasattr(value, "__set__"):
		value.__set__(instance, filteredSettings)
		return
	try:
		getattr(instance, "__dict__")["supportedSettings"] = filteredSettings
	except Exception:
		raise AttributeError("supportedSettings")


def _patchSupportedSettingsClassProperty(synthClass: type) -> None:
	if synthClass in _state._supportedSettingsClassPatches:
		return
	try:
		originalValue = synthClass.__dict__.get("supportedSettings", _state._missingClassAttr)
	except Exception:
		originalValue = _state._missingClassAttr

	def _getSupportedSettings(instance):
		settings = _getOriginalSupportedSettings(instance, synthClass, originalValue)
		if instance is None:
			return settings
		if not bool(_configuration._getConfigValue("enabled", False)):
			return _withoutSonicPitchSettings(settings)
		if not _isGlobalAudioSupportedSynth(_getSynthName(instance)):
			return _withoutSonicPitchSettings(settings)
		return _withSonicPitchSetting(settings)

	def _setSupportedSettings(instance, value):
		_setOriginalSupportedSettings(instance, synthClass, originalValue, value)

	_state._supportedSettingsClassPatches[synthClass] = originalValue
	setattr(
		synthClass,
		"supportedSettings",
		property(
			_getSupportedSettings,
			_setSupportedSettings,
			None,
			getattr(originalValue, "__doc__", None),
		),
	)


def _restoreSupportedSettingsClassProperty(synthClass: type) -> None:
	if synthClass not in _state._supportedSettingsClassPatches:
		return
	originalValue = _state._supportedSettingsClassPatches.pop(synthClass)
	try:
		if originalValue is _state._missingClassAttr:
			delattr(synthClass, "supportedSettings")
		else:
			setattr(synthClass, "supportedSettings", originalValue)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to restore synth supportedSettings property", exc_info=True)


def _restoreAllSupportedSettingsClassProperties() -> None:
	for synthClass in list(_state._supportedSettingsClassPatches):
		_restoreSupportedSettingsClassProperty(synthClass)


def _patchSynthSupportedSettings(synth: Any, setting: Any) -> bool:
	synthClass = synth.__class__
	descriptor = _supportedSettingsDescriptorForClass(synthClass)
	if _isDynamicSupportedSettingsDescriptor(descriptor):
		_patchSupportedSettingsClassProperty(synthClass)
		setattr(synth, _state._SONIC_PITCH_SETTING_PATCHED_ATTR, True)
		return _hasSonicPitchSetting(getattr(synth, "supportedSettings", ()))
	supportedSettings = _withoutSonicPitchSettings(tuple(getattr(synth, "supportedSettings", ())))
	if not getattr(synth, _state._SONIC_PITCH_SETTING_PATCHED_ATTR, False):
		setattr(synth, _state._ORIGINAL_SUPPORTED_SETTINGS_ATTR, supportedSettings)
		synth.supportedSettings = _withSonicPitchSetting(supportedSettings, setting)
		setattr(synth, _state._SONIC_PITCH_SETTING_PATCHED_ATTR, True)
	elif not _hasSonicPitchSetting(supportedSettings):
		synth.supportedSettings = _withSonicPitchSetting(supportedSettings, setting)
	return _hasSonicPitchSetting(getattr(synth, "supportedSettings", ()))


def _stripSonicPitchSetting(synth: Any | None) -> None:
	if synth is None:
		return
	try:
		if synth.__class__ in _state._supportedSettingsClassPatches:
			_restoreSupportedSettingsClassProperty(synth.__class__)
			for attr in (
				_state._ORIGINAL_SUPPORTED_SETTINGS_ATTR,
				_state._SONIC_PITCH_SETTING_PATCHED_ATTR,
			):
				try:
					delattr(synth, attr)
				except Exception:
					pass
			_updateSynthSettingsRing(synth)
			log.info(f"globalSonicPitch: hid Sonic pitch voice setting; synth={_getSynthName(synth)}")
			return
		supportedSettings = tuple(getattr(synth, "supportedSettings", ()))
		filteredSettings = _withoutSonicPitchSettings(supportedSettings)
		if len(filteredSettings) == len(supportedSettings):
			return
		synth.supportedSettings = filteredSettings
		_updateSynthSettingsRing(synth)
		log.info(f"globalSonicPitch: hid Sonic pitch voice setting; synth={_getSynthName(synth)}")
	except Exception:
		log.debugWarning("globalSonicPitch: failed to hide Sonic pitch voice setting", exc_info=True)


def _patchedGetSonicPitchSetting(self):
	pitch = _configuration._getSonicPitchForSynth(self)
	if bool(_configuration._getConfigValue("enabled", False)):
		_host._applyRuntimeSonicPitch(self, pitch)
	return pitch


def _patchedSetSonicPitchSetting(self, value):
	synthName = _getSynthName(self)
	if _dialogs._setVoiceDialogPendingSonicPitch(self, value):
		return None
	pitch = _configuration._setSonicPitchForSynth(self, value)
	if pitch is None:
		return None
	_host._applyRuntimeSonicPitch(self, pitch)
	log.info(
		"globalSonicPitch: captured Sonic pitch setting; "
		f"synth={synthName}; key={_getSonicPitchStorageKey(self)}; sonicPitch={pitch}",
	)
	return None


def _patchSonicPitchClassProperty(synth: Any) -> None:
	synthClass = synth.__class__
	if synthClass not in _state._sonicPitchClassPatches:
		_state._sonicPitchClassPatches[synthClass] = getattr(synthClass, _state.SONIC_PITCH_SETTING_ID, _state._missingClassAttr)
	setattr(
		synthClass,
		_state.SONIC_PITCH_SETTING_ID,
		property(_patchedGetSonicPitchSetting, _patchedSetSonicPitchSetting),
	)


def _refreshSonicPitchAfterVoiceChange(synth: Any | None) -> None:
	if synth is None or not bool(_configuration._getConfigValue("enabled", False)):
		return
	synthName = _getSynthName(synth)
	if not _isGlobalAudioSupportedSynth(synthName):
		return
	try:
		pitch = _configuration._getSonicPitchForSynth(synth)
		_audio._clearIdlePlayerUtterancePitches()
		_host._applyRuntimeSonicPitch(synth, pitch)
		log.info(
			"globalSonicPitch: refreshed Sonic pitch after voice change; "
			f"synth={synthName}; key={_getSonicPitchStorageKey(synth)}; sonicPitch={pitch}",
		)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to refresh Sonic pitch after voice change", exc_info=True)


def _patchSynthVoiceProperty(synth: Any) -> None:
	synthClass = synth.__class__
	if synthClass in _state._voiceClassPatches:
		return
	originalValue = getattr(synthClass, "voice", _state._missingClassAttr)
	if not isinstance(originalValue, property) or originalValue.fset is None:
		return

	def _getVoice(instance):
		if originalValue.fget is None:
			raise AttributeError("voice")
		return originalValue.fget(instance)

	def _setVoice(instance, value):
		originalValue.fset(instance, value)
		_refreshSonicPitchAfterVoiceChange(instance)

	_state._voiceClassPatches[synthClass] = originalValue
	setattr(
		synthClass,
		"voice",
		property(
			_getVoice,
			_setVoice,
			originalValue.fdel,
			originalValue.__doc__,
		),
	)


def _restoreSynthVoiceProperty(synthClass: type) -> None:
	if synthClass not in _state._voiceClassPatches:
		return
	originalValue = _state._voiceClassPatches.pop(synthClass)
	try:
		setattr(synthClass, "voice", originalValue)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to restore synth voice class property", exc_info=True)


def _restoreAllSynthVoiceProperties() -> None:
	for synthClass in list(_state._voiceClassPatches):
		_restoreSynthVoiceProperty(synthClass)


def _patchSynthVariantProperty(synth: Any) -> None:
	synthClass = synth.__class__
	if synthClass in _state._variantClassPatches:
		return
	originalValue = getattr(synthClass, "variant", _state._missingClassAttr)
	if not isinstance(originalValue, property) or originalValue.fset is None:
		return

	def _getVariant(instance):
		if originalValue.fget is None:
			raise AttributeError("variant")
		return originalValue.fget(instance)

	def _setVariant(instance, value):
		originalValue.fset(instance, value)
		_refreshSonicPitchAfterVoiceChange(instance)
		_dialogs._scheduleVoiceDialogSonicPitchControlRefresh(instance)

	_state._variantClassPatches[synthClass] = originalValue
	setattr(
		synthClass,
		"variant",
		property(
			_getVariant,
			_setVariant,
			originalValue.fdel,
			originalValue.__doc__,
		),
	)


def _restoreSynthVariantProperty(synthClass: type) -> None:
	if synthClass not in _state._variantClassPatches:
		return
	originalValue = _state._variantClassPatches.pop(synthClass)
	try:
		setattr(synthClass, "variant", originalValue)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to restore synth variant class property", exc_info=True)


def _restoreAllSynthVariantProperties() -> None:
	for synthClass in list(_state._variantClassPatches):
		_restoreSynthVariantProperty(synthClass)


def _restoreSonicPitchClassProperty(synthClass: type) -> None:
	if synthClass not in _state._sonicPitchClassPatches:
		return
	originalValue = _state._sonicPitchClassPatches.pop(synthClass)
	try:
		if originalValue is _state._missingClassAttr:
			delattr(synthClass, _state.SONIC_PITCH_SETTING_ID)
		else:
			setattr(synthClass, _state.SONIC_PITCH_SETTING_ID, originalValue)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to restore synth Sonic pitch class property", exc_info=True)


def _restoreAllSonicPitchClassProperties() -> None:
	for synthClass in list(_state._sonicPitchClassPatches):
		_restoreSonicPitchClassProperty(synthClass)


def _ensureSynthRingSettingsSelectorIncludesSonicPitch() -> None:
	try:
		if "synthRingSettingsSelector" not in config.conf.spec:
			config.conf.spec["synthRingSettingsSelector"] = {
				"availableSettings": (
					"string_list(default=list('language', 'voice', 'variant', 'rate', "
					"'rateBoost', 'volume', 'pitch', 'inflection', 'sonicPitch'))"
				),
			}
		selectorConfig = config.conf["synthRingSettingsSelector"]
		availableSettings = list(selectorConfig.get("availableSettings", []))
		if _state.SONIC_PITCH_SETTING_ID in availableSettings:
			return
		availableSettings.append(_state.SONIC_PITCH_SETTING_ID)
		selectorConfig["availableSettings"] = availableSettings
		log.info("globalSonicPitch: added Sonic pitch to synthRingSettingsSelector settings list")
	except Exception:
		log.debugWarning("globalSonicPitch: failed to update synthRingSettingsSelector integration", exc_info=True)


def _updateSynthSettingsRing(synth: Any | None) -> None:
	if synth is None or globalVars is None:
		return
	settingsRing = getattr(globalVars, "settingsRing", None)
	if settingsRing is None:
		return
	try:
		settingsRing.updateSupportedSettings(synth)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to update synth settings ring", exc_info=True)


def _getReadableSonicPitchSettingValue(synth: Any) -> int | None:
	try:
		return _configuration._clampPitch(getattr(synth, _state.SONIC_PITCH_SETTING_ID))
	except Exception:
		log.debugWarning("globalSonicPitch: Sonic pitch voice setting is not readable", exc_info=True)
		return None


def _logVoiceSettingOnce(synth: Any, value: int | None = None) -> None:
	synthName = _getSynthName(synth)
	key = _getSonicPitchStorageKey(synth) or synthName
	if key in _state._voiceSettingLogKeys and not _configuration._isDebugLoggingEnabled():
		return
	_state._voiceSettingLogKeys.add(key)
	log.info(
		"globalSonicPitch: added Sonic pitch voice setting; "
		f"synth={synthName or 'unknown'}"
		+ (f"; key={key}" if key else "")
		+ (f"; value={value}" if value is not None else ""),
	)


def _patchSynthSonicPitchSetting(synth: Any | None) -> None:
	if synth is None:
		return
	if not bool(_configuration._getConfigValue("enabled", False)):
		_unpatchSynthSonicPitchSetting(synth)
		return
	synthName = _getSynthName(synth)
	if not _isGlobalAudioSupportedSynth(synthName):
		return
	if _isRemoteSapi32Synth(synthName):
		_host._installSapi32HostDriverPatch()
		if not _host._remoteSapi32SupportsSonicPitch(synth):
			_stripSonicPitchSetting(synth)
			_host._requestRemoteSapi32SynthReload()
			return
	setting = _getSonicPitchDriverSetting()
	if setting is None:
		return
	try:
		_patchSonicPitchClassProperty(synth)
		_patchSynthVoiceProperty(synth)
		_patchSynthVariantProperty(synth)
		if not _patchSynthSupportedSettings(synth, setting):
			return
		settingValue = _getReadableSonicPitchSettingValue(synth)
		if settingValue is None:
			_unpatchSynthSonicPitchSetting(synth)
			return
		_host._applyRuntimeSonicPitch(synth, settingValue)
		_ensureSynthRingSettingsSelectorIncludesSonicPitch()
		_updateSynthSettingsRing(synth)
		_logVoiceSettingOnce(synth, settingValue)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to add Sonic pitch voice setting", exc_info=True)


def _unpatchSynthSonicPitchSetting(synth: Any | None) -> None:
	if synth is None:
		return
	if not getattr(synth, _state._SONIC_PITCH_SETTING_PATCHED_ATTR, False):
		if _isRemoteSapi32Synth(_getSynthName(synth)):
			_stripSonicPitchSetting(synth)
		return
	try:
		if synth.__class__ in _state._supportedSettingsClassPatches:
			_restoreSupportedSettingsClassProperty(synth.__class__)
		else:
			originalSupportedSettings = getattr(synth, _state._ORIGINAL_SUPPORTED_SETTINGS_ATTR, None)
			if originalSupportedSettings is not None:
				synth.supportedSettings = _withoutSonicPitchSettings(originalSupportedSettings)
		for attr in (
			_state._ORIGINAL_SUPPORTED_SETTINGS_ATTR,
			_state._SONIC_PITCH_SETTING_PATCHED_ATTR,
		):
			try:
				delattr(synth, attr)
			except Exception:
				pass
		_restoreSonicPitchClassProperty(synth.__class__)
		_restoreSynthVoiceProperty(synth.__class__)
		_restoreSynthVariantProperty(synth.__class__)
		_updateSynthSettingsRing(synth)
		log.info(f"globalSonicPitch: removed Sonic pitch voice setting; synth={_getSynthName(synth)}")
	except Exception:
		log.debugWarning("globalSonicPitch: failed to remove Sonic pitch voice setting", exc_info=True)


def _patchCurrentSynthPitch() -> None:
	synth = _getCurrentSynth()
	if bool(_configuration._getConfigValue("enabled", False)):
		_patchSynthSonicPitchSetting(synth)
	else:
		_unpatchSynthSonicPitchSetting(synth)
		_restoreAllSupportedSettingsClassProperties()
		_restoreAllSonicPitchClassProperties()
		_restoreAllSynthVoiceProperties()
		_restoreAllSynthVariantProperties()


def _safePatchCurrentSynthPitch() -> None:
	try:
		_patchCurrentSynthPitch()
	except Exception:
		log.debugWarning("globalSonicPitch: failed after synth switch", exc_info=True)


def _schedulePatchCurrentSynthPitch() -> None:
	try:
		wx.CallAfter(_safePatchCurrentSynthPitch)
	except Exception:
		_safePatchCurrentSynthPitch()


def _getCallableSignature(callableObj: Callable[..., Any]) -> inspect.Signature | None:
	try:
		return inspect.signature(callableObj)
	except (TypeError, ValueError):
		return None


def _setWrapperSignature(wrapper: Callable[..., Any], wrapped: Callable[..., Any]) -> None:
	signature = _getCallableSignature(wrapped)
	if signature is None:
		return
	try:
		wrapper.__signature__ = signature
	except Exception:
		pass


def _filterUnsupportedKeywordArguments(
	callableObj: Callable[..., Any],
	kwargs: dict[str, Any],
) -> dict[str, Any]:
	if not kwargs:
		return kwargs
	signature = _getCallableSignature(callableObj)
	if signature is None:
		return kwargs
	parameters = signature.parameters
	if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()):
		return kwargs
	filteredKwargs = {
		name: value
		for name, value in kwargs.items()
		if (
			name in parameters
			and parameters[name].kind
			in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
		)
	}
	if len(filteredKwargs) != len(kwargs) and _configuration._isDebugLoggingEnabled():
		droppedNames = sorted(set(kwargs) - set(filteredKwargs))
		log.debug(
			"globalSonicPitch: filtered unsupported setSynth keyword arguments; "
			f"callable={callableObj!r}; dropped={','.join(droppedNames)}",
		)
	return filteredKwargs


def _resetSynthSwitchRuntimeState() -> None:
	_audio._resetAllPlayerProcessors()
	_state._runtimeSonicPitchByKey.clear()


def _callSetSynthAndPatch(originalSetSynth: Callable[..., Any], *args, **kwargs):
	filteredKwargs = _filterUnsupportedKeywordArguments(originalSetSynth, kwargs)
	sequence, startedAt = _dialogs._beginSynthSwitchDiagnostics("synthDriverHandler.setSynth", args, filteredKwargs)
	_resetSynthSwitchRuntimeState()
	try:
		result = originalSetSynth(*args, **filteredKwargs)
	except Exception as exc:
		_dialogs._finishSynthSwitchDiagnostics(sequence, "synthDriverHandler.setSynth", startedAt, exc)
		raise
	_resetSynthSwitchRuntimeState()
	if not _state._deferSynthPitchPatchDepth:
		_safePatchCurrentSynthPitch()
	_dialogs._finishSynthSwitchDiagnostics(sequence, "synthDriverHandler.setSynth", startedAt)
	return result


def _makeSetSynthWrapper(originalSetSynth: Callable[..., Any]) -> Callable[..., Any]:
	@functools.wraps(originalSetSynth)
	def _globalSonicPitchSetSynthWrapper(*args, **kwargs):
		return _callSetSynthAndPatch(originalSetSynth, *args, **kwargs)

	_setWrapperSignature(_globalSonicPitchSetSynthWrapper, originalSetSynth)
	return _globalSonicPitchSetSynthWrapper


def _callSettingsSetSynthAndPatch(originalSetSynth: Callable[..., Any], *args, **kwargs):
	_state._deferSynthPitchPatchDepth += 1
	sequence = None
	startedAt = None
	try:
		filteredKwargs = _filterUnsupportedKeywordArguments(originalSetSynth, kwargs)
		sequence, startedAt = _dialogs._beginSynthSwitchDiagnostics("settingsDialogs.setSynth", args, filteredKwargs)
		_resetSynthSwitchRuntimeState()
		try:
			result = originalSetSynth(*args, **filteredKwargs)
		except Exception as exc:
			_dialogs._finishSynthSwitchDiagnostics(sequence, "settingsDialogs.setSynth", startedAt, exc)
			raise
		_dialogs._finishSynthSwitchDiagnostics(sequence, "settingsDialogs.setSynth", startedAt)
		return result
	finally:
		_state._deferSynthPitchPatchDepth = max(0, _state._deferSynthPitchPatchDepth - 1)
		_resetSynthSwitchRuntimeState()
		if not _state._deferSynthPitchPatchDepth:
			_safePatchCurrentSynthPitch()


def _makeSettingsSetSynthWrapper(originalSetSynth: Callable[..., Any]) -> Callable[..., Any]:
	@functools.wraps(originalSetSynth)
	def _globalSonicPitchSettingsSetSynthWrapper(*args, **kwargs):
		return _callSettingsSetSynthAndPatch(originalSetSynth, *args, **kwargs)

	_setWrapperSignature(_globalSonicPitchSettingsSetSynthWrapper, originalSetSynth)
	return _globalSonicPitchSettingsSetSynthWrapper


def installSynthPitchHook() -> None:
	if synthDriverHandler is None:
		return
	if getattr(synthDriverHandler, _state._SET_SYNTH_PATCHED_ATTR, False):
		_patchCurrentSynthPitch()
		return
	settingsSetSynth = getattr(settingsDialogs, "setSynth", None)
	originalSetSynth = synthDriverHandler.setSynth
	setSynthWrapper = _makeSetSynthWrapper(originalSetSynth)
	setattr(synthDriverHandler, _state._ORIGINAL_SET_SYNTH_ATTR, originalSetSynth)
	setattr(synthDriverHandler, _state._SET_SYNTH_WRAPPER_ATTR, setSynthWrapper)
	synthDriverHandler.setSynth = setSynthWrapper
	setattr(synthDriverHandler, _state._SET_SYNTH_PATCHED_ATTR, True)
	if callable(settingsSetSynth):
		settingsSetSynthWrapper = _makeSettingsSetSynthWrapper(settingsSetSynth)
		setattr(settingsDialogs, _state._ORIGINAL_SETTINGS_SET_SYNTH_ATTR, settingsSetSynth)
		setattr(settingsDialogs, _state._SETTINGS_SET_SYNTH_WRAPPER_ATTR, settingsSetSynthWrapper)
		settingsDialogs.setSynth = settingsSetSynthWrapper
		setattr(settingsDialogs, _state._SETTINGS_SET_SYNTH_PATCHED_ATTR, True)
	_patchCurrentSynthPitch()
	log.info("globalSonicPitch: installed synth Sonic pitch setting hook")


def uninstallSynthPitchHook() -> None:
	if synthDriverHandler is None:
		return
	_unpatchSynthSonicPitchSetting(_getCurrentSynth())
	_state._runtimeSonicPitchByKey.clear()
	_restoreAllSupportedSettingsClassProperties()
	_restoreAllSonicPitchClassProperties()
	_restoreAllSynthVoiceProperties()
	_restoreAllSynthVariantProperties()
	if getattr(settingsDialogs, _state._SETTINGS_SET_SYNTH_PATCHED_ATTR, False):
		originalSettingsSetSynth = getattr(settingsDialogs, _state._ORIGINAL_SETTINGS_SET_SYNTH_ATTR, None)
		settingsSetSynthWrapper = getattr(settingsDialogs, _state._SETTINGS_SET_SYNTH_WRAPPER_ATTR, None)
		if originalSettingsSetSynth is not None and settingsDialogs.setSynth is settingsSetSynthWrapper:
			settingsDialogs.setSynth = originalSettingsSetSynth
		try:
			delattr(settingsDialogs, _state._ORIGINAL_SETTINGS_SET_SYNTH_ATTR)
		except Exception:
			pass
		try:
			delattr(settingsDialogs, _state._SETTINGS_SET_SYNTH_WRAPPER_ATTR)
		except Exception:
			pass
		setattr(settingsDialogs, _state._SETTINGS_SET_SYNTH_PATCHED_ATTR, False)
	if not getattr(synthDriverHandler, _state._SET_SYNTH_PATCHED_ATTR, False):
		return
	originalSetSynth = getattr(synthDriverHandler, _state._ORIGINAL_SET_SYNTH_ATTR, None)
	setSynthWrapper = getattr(synthDriverHandler, _state._SET_SYNTH_WRAPPER_ATTR, None)
	if originalSetSynth is not None and synthDriverHandler.setSynth is setSynthWrapper:
		synthDriverHandler.setSynth = originalSetSynth
	try:
		delattr(synthDriverHandler, _state._ORIGINAL_SET_SYNTH_ATTR)
	except Exception:
		pass
	try:
		delattr(synthDriverHandler, _state._SET_SYNTH_WRAPPER_ATTR)
	except Exception:
		pass
	setattr(synthDriverHandler, _state._SET_SYNTH_PATCHED_ATTR, False)
	log.info("globalSonicPitch: removed synth Sonic pitch setting hook")
