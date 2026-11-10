"""Main-process integration with the unchanged 32-bit SAPI host wrappers."""

from __future__ import annotations

from ._nvda import (
	Any,
	log,
	os,
	synthDriverHandler,
	wx,
)
from . import configuration as _configuration
from . import native as _native
from . import state as _state
from . import synths as _synths


def _getSapi32HostDriverPath() -> str:
	return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), _state._SAPI32_HOST_DRIVER_DIR)


def _installSapi32HostDriverPatch() -> bool:
	if _native._is32BitProcess():
		return False
	driverPath = _getSapi32HostDriverPath()
	if not os.path.isdir(driverPath):
		log.debugWarning(f"globalSonicPitch: 32-bit host driver path is missing: {driverPath}")
		return False
	patched = False
	try:
		for moduleName in ("sapi4_32", "sapi5_32"):
			try:
				module = __import__(f"synthDrivers.{moduleName}", fromlist=["SynthDriver"])
				synthClass = module.SynthDriver
				if not hasattr(synthClass, _state._ORIGINAL_SAPI32_HOST_PATH_ATTR):
					setattr(synthClass, _state._ORIGINAL_SAPI32_HOST_PATH_ATTR, getattr(synthClass, "synthDriver32Path", None))
				if getattr(synthClass, "synthDriver32Path", None) != driverPath:
					synthClass.synthDriver32Path = driverPath
					log.info(
						"globalSonicPitch: installed 32-bit host driver path; "
						f"synth={moduleName}; path={driverPath}",
					)
				setattr(synthClass, _state._SAPI32_HOST_PATH_PATCHED_ATTR, True)
				patched = True
			except Exception:
				log.debugWarning(f"globalSonicPitch: failed to install 32-bit host path for {moduleName}", exc_info=True)
		return patched
	except Exception:
		log.debugWarning("globalSonicPitch: failed to install 32-bit host driver path", exc_info=True)
		return False


def _restoreSapi32HostDriverPatch() -> None:
	if _native._is32BitProcess():
		return
	for moduleName in ("sapi4_32", "sapi5_32"):
		try:
			module = __import__(f"synthDrivers.{moduleName}", fromlist=["SynthDriver"])
			synthClass = module.SynthDriver
			if not getattr(synthClass, _state._SAPI32_HOST_PATH_PATCHED_ATTR, False):
				continue
			originalPath = getattr(synthClass, _state._ORIGINAL_SAPI32_HOST_PATH_ATTR, None)
			if originalPath:
				synthClass.synthDriver32Path = originalPath
			for attr in (_state._ORIGINAL_SAPI32_HOST_PATH_ATTR, _state._SAPI32_HOST_PATH_PATCHED_ATTR):
				try:
					delattr(synthClass, attr)
				except Exception:
					pass
			log.info(f"globalSonicPitch: restored 32-bit host driver path; synth={moduleName}")
		except Exception:
			log.debugWarning(f"globalSonicPitch: failed to restore 32-bit host path for {moduleName}", exc_info=True)


def _getRemoteService(synth: Any | None) -> Any | None:
	if synth is None:
		return None
	return getattr(synth, "_remoteService", None)


def _remoteSapi32SupportsSonicPitch(synth: Any | None) -> bool:
	if not _synths._isRemoteSapi32Synth(_synths._getSynthName(synth)):
		return False
	return _synths._hasSonicPitchSetting(getattr(synth, "supportedSettings", ()))


def _reloadCurrentRemoteSapi32Synth() -> None:
	if synthDriverHandler is None or _state._sapi32HostReloading:
		return
	synthName = _synths._getSynthName()
	if not _synths._isRemoteSapi32Synth(synthName):
		return
	_state._sapi32HostReloading = True
	try:
		log.info(f"globalSonicPitch: reloading 32-bit synth to enable host Sonic pitch support; synth={synthName}")
		synthDriverHandler.setSynth(synthName)
	finally:
		_state._sapi32HostReloading = False
		_state._sapi32HostReloadRequested = False


def _requestRemoteSapi32SynthReload() -> None:
	if _state._sapi32HostReloadRequested or not _installSapi32HostDriverPatch():
		return
	if not _synths._isRemoteSapi32Synth(_synths._getSynthName()):
		return
	_state._sapi32HostReloadRequested = True
	try:
		wx.CallAfter(_reloadCurrentRemoteSapi32Synth)
	except Exception:
		_reloadCurrentRemoteSapi32Synth()


def _setRemoteSapi32SonicPitch(synth: Any | None, pitch: int | float) -> bool:
	if not _synths._isRemoteSapi32Synth(_synths._getSynthName(synth)):
		return False
	service = _getRemoteService(synth)
	if service is None:
		return False
	pitch = _configuration._clampPitch(pitch)
	quality = _configuration._getSonicQuality()
	try:
		service.setParam(_state.SONIC_PITCH_EXTENDED_RANGE_PARAM_ID, 1 if _configuration._isExtendedPitchRangeEnabled() else 0)
	except Exception:
		log.debugWarning(
			"globalSonicPitch: failed to apply remote 32-bit Sonic pitch range",
			exc_info=True,
		)
	try:
		service.setParam(_state.SONIC_QUALITY_PARAM_ID, quality)
	except Exception:
		log.debugWarning(
			"globalSonicPitch: failed to apply remote 32-bit Sonic quality; remote host will use fast mode",
			exc_info=True,
		)
	try:
		service.setParam(_state.SONIC_PITCH_SETTING_ID, pitch)
		log.info(
			"globalSonicPitch: applied remote 32-bit Sonic pitch; "
			f"synth={_synths._getSynthName(synth)}; sonicPitch={pitch}; "
			f"extendedRange={_configuration._isExtendedPitchRangeEnabled()}; quality={quality} ({_configuration._getQualityLabel(quality)})",
		)
		return True
	except Exception:
		log.debugWarning("globalSonicPitch: failed to apply remote 32-bit Sonic pitch", exc_info=True)
		return False


def _applyRuntimeSonicPitch(synth: Any | None, pitch: int | float) -> None:
	if not _synths._isRemoteSapi32Synth(_synths._getSynthName(synth)):
		return
	key = _synths._getSonicPitchStorageKey(synth) or _synths._getSynthName(synth)
	pitch = _configuration._clampPitch(pitch)
	state = (pitch, _configuration._isExtendedPitchRangeEnabled(), _configuration._getSonicQuality())
	if key and _state._runtimeSonicPitchByKey.get(key) == state:
		return
	if _setRemoteSapi32SonicPitch(synth, pitch):
		if key:
			_state._runtimeSonicPitchByKey[key] = state
	else:
		_requestRemoteSapi32SynthReload()
