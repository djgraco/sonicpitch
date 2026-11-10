"""Voice-setting transactions, refresh guards and dialog cleanup."""

from __future__ import annotations

from ._nvda import (
	Any,
	Callable,
	functools,
	log,
	settingsDialogs,
	threading,
	time,
	weakref,
	wx,
)
from . import audio as _audio
from . import configuration as _configuration
from . import host as _host
from . import state as _state
from . import synths as _synths


def _getActiveVoiceDialogSession() -> dict[str, dict[str, int]] | None:
	if not _state._voiceDialogSessions:
		return None
	try:
		return next(reversed(_state._voiceDialogSessions.values()))
	except Exception:
		return None


def _getVoiceDialogPendingPitch(key: str) -> int | None:
	for session in reversed(tuple(_state._voiceDialogSessions.values())):
		pending = session.get("pending", {})
		if key in pending:
			return _configuration._clampPitch(pending[key])
	return None


def _captureVoiceDialogBaseline(session: dict[str, dict[str, int]], synthOrName: Any | None) -> str:
	key = _synths._getSonicPitchStorageKey(synthOrName)
	if not key:
		return ""
	snapshots = session.setdefault("snapshots", {})
	if key not in snapshots:
		snapshots[key] = _configuration._getStoredSonicPitchForKey(key)
	return key


def _setVoiceDialogPendingSonicPitch(synth: Any | None, pitch: int | float) -> bool:
	session = _getActiveVoiceDialogSession()
	if session is None:
		return False
	synthName = _synths._getSynthName(synth)
	if not _synths._isGlobalAudioSupportedSynth(synthName):
		return False
	key = _captureVoiceDialogBaseline(session, synth)
	if not key:
		return False
	pitch = _configuration._clampPitch(pitch)
	pending = session.setdefault("pending", {})
	snapshotPitch = session.setdefault("snapshots", {}).get(key, _state.NEUTRAL_PITCH)
	if key not in pending and pitch == snapshotPitch:
		return True
	pending[key] = pitch
	_audio._clearIdlePlayerUtterancePitches()
	_host._applyRuntimeSonicPitch(synth, pitch)
	log.info(
		"globalSonicPitch: captured temporary Sonic pitch setting; "
		f"synth={synthName}; key={key}; pendingPitch={pitch}",
	)
	return True


def _commitVoiceDialogSession(panelId: int) -> None:
	session = _state._voiceDialogSessions.get(panelId)
	if not session:
		return
	pending = dict(session.get("pending", {}))
	session["pending"] = {}
	for key, pitch in pending.items():
		_configuration._setSonicPitchForKey(key, pitch)
	currentSynth = _synths._getCurrentSynth()
	currentKey = _synths._getSonicPitchStorageKey(currentSynth)
	if currentKey in pending:
		_host._applyRuntimeSonicPitch(currentSynth, pending[currentKey])
	snapshots = session.setdefault("snapshots", {})
	for key in set(snapshots) | set(pending):
		snapshots[key] = _configuration._getStoredSonicPitchForKey(key)
	if pending:
		log.info(
			"globalSonicPitch: committed Sonic pitch changes from Voice settings; "
			f"keys={','.join(sorted(pending))}",
		)


def _restoreVoiceDialogSession(panelId: int) -> None:
	session = _state._voiceDialogSessions.get(panelId)
	if not session:
		return
	pending = dict(session.get("pending", {}))
	snapshots = dict(session.get("snapshots", {}))
	session["pending"] = {}
	if not pending:
		return
	_audio._clearIdlePlayerUtterancePitches()
	for key, pitch in snapshots.items():
		_configuration._setSonicPitchForKey(key, pitch)
	currentSynth = _synths._getCurrentSynth()
	currentKey = _synths._getSonicPitchStorageKey(currentSynth)
	if currentKey in snapshots:
		_host._applyRuntimeSonicPitch(currentSynth, snapshots[currentKey])
	log.info(
		"globalSonicPitch: restored Sonic pitch after Voice settings discard; "
		f"keys={','.join(sorted(pending))}",
	)


def _ensureVoiceDialogSession(panel: Any) -> None:
	panelId = id(panel)
	if panelId not in _state._voiceDialogSessions:
		_state._voiceDialogSessions[panelId] = {"snapshots": {}, "pending": {}}
	_captureVoiceDialogBaseline(_state._voiceDialogSessions[panelId], _synths._getCurrentSynth())
	_state._voiceDialogPanelRefs[panelId] = weakref.ref(panel)
	try:
		setattr(panel, "_globalSonicPitchVoicePanelReleased", False)
	except Exception:
		pass
	if getattr(panel, "_globalSonicPitchVoiceSessionDestroyBound", False):
		return
	panelRef = weakref.ref(panel)

	def _onDestroy(evt):
		try:
			targetPanel = panelRef()
			if targetPanel is not None and evt.GetEventObject() is targetPanel:
				try:
					_restoreVoiceDialogSession(panelId)
				except Exception:
					log.debugWarning("globalSonicPitch: failed to restore Voice settings on destroy", exc_info=True)
				finally:
					_state._voiceDialogSessions.pop(panelId, None)
					_releaseVoiceDialogPanel(targetPanel)
		finally:
			evt.Skip()

	try:
		panel.Bind(wx.EVT_WINDOW_DESTROY, _onDestroy)
		setattr(panel, "_globalSonicPitchVoiceSessionDestroyBound", True)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to bind Voice settings destroy handler", exc_info=True)


def _releaseVoiceDialogPanel(panel: Any) -> None:
	_state._voiceDialogPanelRefs.pop(id(panel), None)
	try:
		setattr(panel, "_globalSonicPitchVoicePanelReleased", True)
	except Exception:
		pass
	try:
		setattr(panel, "_currentSettingsRef", lambda: True)
	except Exception:
		pass
	_scheduleSettingsDialogGarbageCollection("voice panel released")


def _refreshVoiceDialogSonicPitchControls() -> None:
	_state._voiceDialogSonicPitchRefreshPending = False
	for panelId, panelRef in list(_state._voiceDialogPanelRefs.items()):
		panel = panelRef()
		if panel is None or panelId not in _state._voiceDialogSessions:
			_state._voiceDialogPanelRefs.pop(panelId, None)
			continue
		if getattr(panel, "_globalSonicPitchVoicePanelReleased", False):
			_state._voiceDialogPanelRefs.pop(panelId, None)
			continue
		try:
			if getattr(panel, "IsBeingDeleted", lambda: False)():
				_state._voiceDialogPanelRefs.pop(panelId, None)
				continue
		except Exception:
			pass
		try:
			panel.updateDriverSettings(changedSetting="variant")
		except Exception:
			log.debugWarning(
				"globalSonicPitch: failed to refresh Sonic pitch control after variant change",
				exc_info=True,
			)


def _scheduleVoiceDialogSonicPitchControlRefresh(synth: Any | None) -> None:
	if not _state._voiceDialogSessions or synth is None:
		return
	if not bool(_configuration._getConfigValue("enabled", False)):
		return
	if not _synths._isGlobalAudioSupportedSynth(_synths._getSynthName(synth)):
		return
	for session in list(_state._voiceDialogSessions.values()):
		try:
			_captureVoiceDialogBaseline(session, synth)
		except Exception:
			log.debugWarning(
				"globalSonicPitch: failed to capture Voice settings baseline after variant change",
				exc_info=True,
			)
	if _state._voiceDialogSonicPitchRefreshPending:
		return
	_state._voiceDialogSonicPitchRefreshPending = True
	try:
		wx.CallAfter(_refreshVoiceDialogSonicPitchControls)
	except Exception:
		_refreshVoiceDialogSonicPitchControls()


def _formatDiagnosticAge(timestamp: float | None) -> str:
	if timestamp is None:
		return "none"
	try:
		return f"{max(0.0, time.monotonic() - timestamp):.3f}s"
	except Exception:
		return "unknown"


def _getRequestedSynthNameFromCall(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
	value = None
	if args:
		value = args[0]
	else:
		for key in ("name", "synthName", "synth"):
			if key in kwargs:
				value = kwargs[key]
				break
	if value is None:
		return ""
	if isinstance(value, str):
		return value
	return _synths._getSynthName(value)


def _beginSynthSwitchDiagnostics(
	source: str,
	args: tuple[Any, ...],
	kwargs: dict[str, Any],
) -> tuple[int, float]:
	_state._synthSwitchDiagnosticSequence += 1
	sequence = _state._synthSwitchDiagnosticSequence
	startedAt = time.monotonic()
	beforeSynth = _synths._getSynthName()
	requestedSynth = _getRequestedSynthNameFromCall(args, kwargs)
	_state._lastSynthSwitchStartedAt = startedAt
	_state._lastSynthSwitchCompletedAt = None
	_state._lastSynthSwitchSource = source
	_state._lastSynthSwitchRequestedSynth = requestedSynth
	_state._lastSynthSwitchBeforeSynth = beforeSynth
	_state._lastSynthSwitchAfterSynth = ""
	_state._lastSynthSwitchFailed = False
	log.info(
		"globalSonicPitch: setSynth diagnostic start; "
		f"sequence={sequence}; source={source}; requestedSynth={requestedSynth or 'unknown'}; "
		f"beforeSynth={beforeSynth or 'unknown'}; remoteBefore={_synths._isRemoteSapi32Synth(beforeSynth)}"
	)
	return sequence, startedAt


def _finishSynthSwitchDiagnostics(
	sequence: int,
	source: str,
	startedAt: float,
	error: BaseException | None = None,
) -> None:
	completedAt = time.monotonic()
	afterSynth = _synths._getSynthName()
	_state._lastSynthSwitchCompletedAt = completedAt
	_state._lastSynthSwitchAfterSynth = afterSynth
	_state._lastSynthSwitchFailed = error is not None
	log.info(
		"globalSonicPitch: setSynth diagnostic end; "
		f"sequence={sequence}; source={source}; afterSynth={afterSynth or 'unknown'}; "
		f"remoteAfter={_synths._isRemoteSapi32Synth(afterSynth)}; elapsedMs={(completedAt - startedAt) * 1000.0:.1f}; "
		f"failed={error is not None}; errorType={type(error).__name__ if error is not None else 'none'}"
	)


def _getSynthSwitchDiagnosticState() -> str:
	return (
		f"synthSwitchSequence={_state._synthSwitchDiagnosticSequence}; "
		f"synthSwitchSource={_state._lastSynthSwitchSource or 'none'}; "
		f"requestedSynth={_state._lastSynthSwitchRequestedSynth or 'unknown'}; "
		f"beforeSynth={_state._lastSynthSwitchBeforeSynth or 'unknown'}; "
		f"afterSynth={_state._lastSynthSwitchAfterSynth or 'unknown'}; "
		f"sinceSwitchStart={_formatDiagnosticAge(_state._lastSynthSwitchStartedAt)}; "
		f"sinceSwitchEnd={_formatDiagnosticAge(_state._lastSynthSwitchCompletedAt)}; "
		f"synthSwitchFailed={_state._lastSynthSwitchFailed}"
	)


def _getVoiceDialogPanelDiagnosticCounts() -> tuple[int, int, int]:
	alive = 0
	dead = 0
	released = 0
	for panelRef in list(_state._voiceDialogPanelRefs.values()):
		try:
			panel = panelRef()
		except Exception:
			dead += 1
			continue
		if panel is None:
			dead += 1
			continue
		alive += 1
		if getattr(panel, "_globalSonicPitchVoicePanelReleased", False):
			released += 1
	return alive, dead, released


def _getSettingsDialogCleanupDiagnosticState(reason: str) -> str:
	synthName = _synths._getSynthName()
	aliveRefs, deadRefs, releasedRefs = _getVoiceDialogPanelDiagnosticCounts()
	return (
		f"reason={reason}; currentSynth={synthName or 'unknown'}; "
		f"remoteSapi32={_synths._isRemoteSapi32Synth(synthName)}; "
		f"voiceDialogSessions={len(_state._voiceDialogSessions)}; "
		f"panelRefs={len(_state._voiceDialogPanelRefs)}; alivePanelRefs={aliveRefs}; "
		f"deadPanelRefs={deadRefs}; releasedPanelRefs={releasedRefs}; "
		f"pendingGc={_state._settingsDialogGcPending}; thread={threading.current_thread().name}; "
		f"{_getSynthSwitchDiagnosticState()}"
	)


def _isDestroyedSettingsDialogState(settingsDialogClass: Any, state: Any) -> bool:
	try:
		return state is settingsDialogClass.DialogState.DESTROYED or state == settingsDialogClass.DialogState.DESTROYED
	except Exception:
		return False


def _isDestroyedWxDialog(dialog: Any) -> bool:
	try:
		if not bool(dialog):
			return True
	except Exception:
		return True
	try:
		isBeingDeleted = getattr(dialog, "IsBeingDeleted", None)
		if callable(isBeingDeleted) and isBeingDeleted():
			return True
	except Exception:
		return True
	return False


def _purgeDestroyedSettingsDialogInstances(reason: str) -> int:
	settingsDialogClass = getattr(settingsDialogs, "SettingsDialog", None)
	if settingsDialogClass is None:
		return 0
	instances = getattr(settingsDialogClass, "_instances", None)
	if instances is None:
		return 0
	try:
		instanceItems = list(instances.items())
	except Exception:
		log.debugWarning("globalSonicPitch: failed to inspect destroyed settings dialogs", exc_info=True)
		return 0
	purged = 0
	for dialog, state in instanceItems:
		if not _isDestroyedSettingsDialogState(settingsDialogClass, state):
			continue
		if not _isDestroyedWxDialog(dialog):
			continue
		try:
			instances.pop(dialog, None)
		except Exception:
			log.debugWarning("globalSonicPitch: failed to purge destroyed settings dialog instance", exc_info=True)
			continue
		purged += 1
	if purged:
		log.info(
			"globalSonicPitch: purged destroyed settings dialog registry entries; "
			f"purged={purged}; {_getSettingsDialogCleanupDiagnosticState(reason)}"
		)
	return purged


def _makeAutoSettingsRefreshGuiGuard(originalRefreshGui: Callable[..., Any]) -> Callable[..., Any]:
	@functools.wraps(originalRefreshGui)
	def _globalSonicPitchAutoSettingsRefreshGuiGuard(self, *args, **kwargs):
		if getattr(self, "_globalSonicPitchVoicePanelReleased", False):
			return None
		try:
			return originalRefreshGui(self, *args, **kwargs)
		except RuntimeError as exc:
			if "has been deleted" not in str(exc):
				raise
			log.debug("globalSonicPitch: ignored refresh for destroyed NVDA auto settings panel", exc_info=True)
			return None

	return _globalSonicPitchAutoSettingsRefreshGuiGuard


def _collectSettingsDialogGarbage(reason: str = "unknown") -> None:
	_state._settingsDialogGcPending = False
	log.info(
		"globalSonicPitch: settings dialog cleanup start; "
		f"{_getSettingsDialogCleanupDiagnosticState(reason)}"
	)
	purged = _purgeDestroyedSettingsDialogInstances(reason)
	log.info(
		"globalSonicPitch: settings dialog cleanup end; "
		f"purged={purged}; forcedGc=False; {_getSettingsDialogCleanupDiagnosticState(reason)}"
	)


def _scheduleSettingsDialogGarbageCollection(reason: str = "unknown") -> None:
	if _state._settingsDialogGcPending:
		log.info(
			"globalSonicPitch: settings dialog cleanup already pending; "
			f"{_getSettingsDialogCleanupDiagnosticState(reason)}"
		)
		return
	_state._settingsDialogGcPending = True
	log.info(
		"globalSonicPitch: settings dialog cleanup scheduled; "
		f"{_getSettingsDialogCleanupDiagnosticState(reason)}"
	)
	try:
		wx.CallAfter(_collectSettingsDialogGarbage, reason)
	except Exception:
		_collectSettingsDialogGarbage(reason)


def _makeSettingsDialogDestroyedStateWrapper(originalDestroyedState: Callable[..., Any]) -> Callable[..., Any]:
	@functools.wraps(originalDestroyedState)
	def _globalSonicPitchSettingsDialogDestroyedState(self, *args, **kwargs):
		try:
			return originalDestroyedState(self, *args, **kwargs)
		finally:
			_scheduleSettingsDialogGarbageCollection("settings dialog destroyed")

	return _globalSonicPitchSettingsDialogDestroyedState


def _installSettingsDialogDestroyedStateGuard() -> None:
	settingsDialogClass = getattr(settingsDialogs, "SettingsDialog", None)
	if settingsDialogClass is None:
		return
	if getattr(settingsDialogClass, _state._SETTINGS_DIALOG_DESTROYED_STATE_PATCHED_ATTR, False):
		return
	originalDestroyedState = getattr(settingsDialogClass, "_setInstanceDestroyedState", None)
	if originalDestroyedState is None:
		return
	destroyedStateWrapper = _makeSettingsDialogDestroyedStateWrapper(originalDestroyedState)
	setattr(settingsDialogClass, _state._ORIGINAL_SETTINGS_DIALOG_DESTROYED_STATE_ATTR, originalDestroyedState)
	setattr(settingsDialogClass, _state._SETTINGS_DIALOG_DESTROYED_STATE_WRAPPER_ATTR, destroyedStateWrapper)
	settingsDialogClass._setInstanceDestroyedState = destroyedStateWrapper
	setattr(settingsDialogClass, _state._SETTINGS_DIALOG_DESTROYED_STATE_PATCHED_ATTR, True)


def _uninstallSettingsDialogDestroyedStateGuard() -> None:
	settingsDialogClass = getattr(settingsDialogs, "SettingsDialog", None)
	if settingsDialogClass is None:
		return
	if not getattr(settingsDialogClass, _state._SETTINGS_DIALOG_DESTROYED_STATE_PATCHED_ATTR, False):
		return
	originalDestroyedState = getattr(settingsDialogClass, _state._ORIGINAL_SETTINGS_DIALOG_DESTROYED_STATE_ATTR, None)
	destroyedStateWrapper = getattr(settingsDialogClass, _state._SETTINGS_DIALOG_DESTROYED_STATE_WRAPPER_ATTR, None)
	if originalDestroyedState is not None and settingsDialogClass._setInstanceDestroyedState is destroyedStateWrapper:
		settingsDialogClass._setInstanceDestroyedState = originalDestroyedState
	for attr in (
		_state._ORIGINAL_SETTINGS_DIALOG_DESTROYED_STATE_ATTR,
		_state._SETTINGS_DIALOG_DESTROYED_STATE_WRAPPER_ATTR,
	):
		try:
			delattr(settingsDialogClass, attr)
		except Exception:
			pass
	setattr(settingsDialogClass, _state._SETTINGS_DIALOG_DESTROYED_STATE_PATCHED_ATTR, False)


def _installAutoSettingsRefreshGuiGuard() -> None:
	autoSettingsMixin = getattr(settingsDialogs, "AutoSettingsMixin", None)
	if autoSettingsMixin is None:
		return
	if getattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_PATCHED_ATTR, False):
		return
	originalRefreshGui = autoSettingsMixin.refreshGui
	refreshGuiGuard = _makeAutoSettingsRefreshGuiGuard(originalRefreshGui)
	setattr(autoSettingsMixin, _state._ORIGINAL_AUTO_SETTINGS_REFRESH_GUI_ATTR, originalRefreshGui)
	setattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_WRAPPER_ATTR, refreshGuiGuard)
	autoSettingsMixin.refreshGui = refreshGuiGuard
	setattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_PATCHED_ATTR, True)


def _uninstallAutoSettingsRefreshGuiGuard() -> None:
	autoSettingsMixin = getattr(settingsDialogs, "AutoSettingsMixin", None)
	if autoSettingsMixin is None:
		return
	if not getattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_PATCHED_ATTR, False):
		return
	originalRefreshGui = getattr(autoSettingsMixin, _state._ORIGINAL_AUTO_SETTINGS_REFRESH_GUI_ATTR, None)
	refreshGuiGuard = getattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_WRAPPER_ATTR, None)
	if originalRefreshGui is not None and autoSettingsMixin.refreshGui is refreshGuiGuard:
		autoSettingsMixin.refreshGui = originalRefreshGui
	try:
		delattr(autoSettingsMixin, _state._ORIGINAL_AUTO_SETTINGS_REFRESH_GUI_ATTR)
	except Exception:
		pass
	try:
		delattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_WRAPPER_ATTR)
	except Exception:
		pass
	setattr(autoSettingsMixin, _state._AUTO_SETTINGS_REFRESH_GUI_PATCHED_ATTR, False)


def _patchedVoicePanelMakeSettings(self, *args, **kwargs):
	_ensureVoiceDialogSession(self)
	originalMakeSettings = getattr(settingsDialogs.VoiceSettingsPanel, _state._ORIGINAL_VOICE_PANEL_MAKE_SETTINGS_ATTR)
	return originalMakeSettings(self, *args, **kwargs)


def _patchedVoicePanelOnSave(self, *args, **kwargs):
	originalOnSave = getattr(settingsDialogs.VoiceSettingsPanel, _state._ORIGINAL_VOICE_PANEL_ON_SAVE_ATTR)
	result = originalOnSave(self, *args, **kwargs)
	panelId = id(self)
	try:
		_commitVoiceDialogSession(panelId)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to commit Voice settings Sonic pitch transaction", exc_info=True)
	finally:
		_state._voiceDialogSessions.pop(panelId, None)
		_releaseVoiceDialogPanel(self)
	return result


def _patchedVoicePanelOnDiscard(self, *args, **kwargs):
	originalOnDiscard = getattr(settingsDialogs.VoiceSettingsPanel, _state._ORIGINAL_VOICE_PANEL_ON_DISCARD_ATTR)
	try:
		return originalOnDiscard(self, *args, **kwargs)
	finally:
		panelId = id(self)
		try:
			_restoreVoiceDialogSession(panelId)
		except Exception:
			log.debugWarning("globalSonicPitch: failed to discard Voice settings Sonic pitch transaction", exc_info=True)
		finally:
			_state._voiceDialogSessions.pop(panelId, None)
			_releaseVoiceDialogPanel(self)


def installVoiceSettingsDialogHook() -> None:
	voicePanelClass = getattr(settingsDialogs, "VoiceSettingsPanel", None)
	if voicePanelClass is None:
		return
	if getattr(voicePanelClass, _state._VOICE_PANEL_PATCHED_ATTR, False):
		return
	_installSettingsDialogDestroyedStateGuard()
	_installAutoSettingsRefreshGuiGuard()
	setattr(voicePanelClass, _state._ORIGINAL_VOICE_PANEL_MAKE_SETTINGS_ATTR, voicePanelClass.makeSettings)
	setattr(voicePanelClass, _state._ORIGINAL_VOICE_PANEL_ON_SAVE_ATTR, voicePanelClass.onSave)
	setattr(voicePanelClass, _state._ORIGINAL_VOICE_PANEL_ON_DISCARD_ATTR, voicePanelClass.onDiscard)
	voicePanelClass.makeSettings = _patchedVoicePanelMakeSettings
	voicePanelClass.onSave = _patchedVoicePanelOnSave
	voicePanelClass.onDiscard = _patchedVoicePanelOnDiscard
	setattr(voicePanelClass, _state._VOICE_PANEL_PATCHED_ATTR, True)
	log.info("globalSonicPitch: installed Voice settings Sonic pitch transaction hook")


def uninstallVoiceSettingsDialogHook() -> None:
	voicePanelClass = getattr(settingsDialogs, "VoiceSettingsPanel", None)
	if voicePanelClass is None:
		return
	for panelId in list(_state._voiceDialogSessions):
		try:
			_restoreVoiceDialogSession(panelId)
		except Exception:
			log.debugWarning("globalSonicPitch: failed to restore Voice settings while uninstalling hook", exc_info=True)
		finally:
			_state._voiceDialogSessions.pop(panelId, None)
			panelRef = _state._voiceDialogPanelRefs.get(panelId)
			panel = panelRef() if panelRef is not None else None
			if panel is not None:
				_releaseVoiceDialogPanel(panel)
			else:
				_state._voiceDialogPanelRefs.pop(panelId, None)
	if not getattr(voicePanelClass, _state._VOICE_PANEL_PATCHED_ATTR, False):
		_uninstallAutoSettingsRefreshGuiGuard()
		_uninstallSettingsDialogDestroyedStateGuard()
		return
	originalMakeSettings = getattr(voicePanelClass, _state._ORIGINAL_VOICE_PANEL_MAKE_SETTINGS_ATTR, None)
	originalOnSave = getattr(voicePanelClass, _state._ORIGINAL_VOICE_PANEL_ON_SAVE_ATTR, None)
	originalOnDiscard = getattr(voicePanelClass, _state._ORIGINAL_VOICE_PANEL_ON_DISCARD_ATTR, None)
	if originalMakeSettings is not None and voicePanelClass.makeSettings is _patchedVoicePanelMakeSettings:
		voicePanelClass.makeSettings = originalMakeSettings
	if originalOnSave is not None and voicePanelClass.onSave is _patchedVoicePanelOnSave:
		voicePanelClass.onSave = originalOnSave
	if originalOnDiscard is not None and voicePanelClass.onDiscard is _patchedVoicePanelOnDiscard:
		voicePanelClass.onDiscard = originalOnDiscard
	for attr in (
		_state._ORIGINAL_VOICE_PANEL_MAKE_SETTINGS_ATTR,
		_state._ORIGINAL_VOICE_PANEL_ON_SAVE_ATTR,
		_state._ORIGINAL_VOICE_PANEL_ON_DISCARD_ATTR,
	):
		try:
			delattr(voicePanelClass, attr)
		except Exception:
			pass
	setattr(voicePanelClass, _state._VOICE_PANEL_PATCHED_ATTR, False)
	_uninstallAutoSettingsRefreshGuiGuard()
	_uninstallSettingsDialogDestroyedStateGuard()
	log.info("globalSonicPitch: removed Voice settings Sonic pitch transaction hook")
