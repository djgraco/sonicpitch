"""Speech WavePlayer hooks, buffering and completion callbacks."""

from __future__ import annotations

from ._nvda import (
	Any,
	Callable,
	ctypes,
	inspect,
	log,
	nvwave,
)
from . import configuration as _configuration
from . import native as _native
from . import state as _state
from . import synths as _synths


def _getProcessingContext(player: nvwave.WavePlayer, rawSize: int) -> tuple[str, int, int] | None:
	if rawSize <= 0:
		return None
	if not bool(_configuration._getConfigValue("enabled", False)):
		return None
	if not _isSpeechPlayer(player):
		return None
	synth = _synths._getCurrentSynth()
	synthName = _synths._getSynthName(synth)
	if not _synths._isGlobalAudioSupportedSynth(synthName):
		return None
	if _synths._isRemoteSapi32Synth(synthName):
		return None
	pitch = _configuration._getSonicPitchForSynth(synth)
	utterancePitch = _getOrCreatePlayerUtterancePitch(player, pitch)
	quality = _configuration._getSonicQuality()
	utteranceQuality = _getOrCreatePlayerUtteranceQuality(player, quality)
	if utterancePitch != pitch:
		_logDeferredPitchOnce(synthName, utterancePitch, pitch)
	if utteranceQuality != quality:
		_logDeferredQualityOnce(synthName, utteranceQuality, quality)
	if utterancePitch == _state.NEUTRAL_PITCH:
		_clearPlayerUtterancePitch(player)
		return None
	return synthName, utterancePitch, utteranceQuality


def _isSpeechPlayer(player: nvwave.WavePlayer) -> bool:
	try:
		return getattr(player, "_purpose", None) == nvwave.AudioPurpose.SPEECH
	except Exception:
		return False


def _getWaveFormat(player: nvwave.WavePlayer) -> tuple[int, int, int] | None:
	try:
		waveFormat = player._format
		channels = int(waveFormat.nChannels)
		sampleRate = int(waveFormat.nSamplesPerSec)
		bitsPerSample = int(waveFormat.wBitsPerSample)
	except Exception:
		return None
	if channels <= 0 or sampleRate <= 0:
		return None
	return channels, sampleRate, bitsPerSample


def _getRawBytes(data: Any, size: int | None) -> bytes | None:
	try:
		if size is not None:
			size = int(size)
			if size < 0:
				return None
			if isinstance(data, (bytes, bytearray, memoryview)):
				return bytes(data)[:size]
			return ctypes.string_at(data, size)
		if isinstance(data, bytes):
			return data
		if isinstance(data, (bytearray, memoryview)):
			return bytes(data)
		return bytes(data)
	except Exception:
		return None


def _getPlayerProcessorKey(player: nvwave.WavePlayer) -> int:
	return id(player)


def _finishProcessorSafely(processor: "_SonicStreamProcessor" | None) -> bytes:
	if processor is None:
		return b""
	try:
		return processor.finish()
	except Exception:
		log.debugWarning("globalSonicPitch: failed to finish retired Sonic stream", exc_info=True)
		return b""


def _finishPlayerProcessor(player: nvwave.WavePlayer) -> tuple[bytes, Callable[..., None] | None]:
	with _state._playerProcessorsLock:
		processor = _state._playerProcessors.get(_getPlayerProcessorKey(player))
	if processor is None:
		return b"", None
	return _finishProcessorSafely(processor), processor.takeOnDone()


def _resetPlayerProcessor(player: nvwave.WavePlayer) -> None:
	with _state._playerProcessorsLock:
		processorKey = _getPlayerProcessorKey(player)
		processor = _state._playerProcessors.pop(processorKey, None)
		_state._playerUtterancePitches.pop(processorKey, None)
		_state._playerUtteranceQualities.pop(processorKey, None)
	if processor is not None:
		processor.completePendingOnDone()


def _resetAllPlayerProcessors() -> None:
	with _state._playerProcessorsLock:
		processors = list(_state._playerProcessors.values())
		_state._playerProcessors.clear()
		_state._playerUtterancePitches.clear()
		_state._playerUtteranceQualities.clear()
	for processor in processors:
		_finishProcessorSafely(processor)
		processor.completePendingOnDone()


def _getOrCreatePlayerUtterancePitch(player: nvwave.WavePlayer, pitch: int) -> int:
	with _state._playerProcessorsLock:
		processorKey = _getPlayerProcessorKey(player)
		if processorKey not in _state._playerUtterancePitches:
			_state._playerUtterancePitches[processorKey] = _configuration._clampPitch(pitch)
		return _state._playerUtterancePitches[processorKey]


def _getOrCreatePlayerUtteranceQuality(player: nvwave.WavePlayer, quality: int) -> int:
	with _state._playerProcessorsLock:
		processorKey = _getPlayerProcessorKey(player)
		if processorKey not in _state._playerUtteranceQualities:
			_state._playerUtteranceQualities[processorKey] = _configuration._clampQuality(quality)
		return _state._playerUtteranceQualities[processorKey]


def _clearPlayerUtterancePitch(player: nvwave.WavePlayer) -> None:
	with _state._playerProcessorsLock:
		processorKey = _getPlayerProcessorKey(player)
		_state._playerUtterancePitches.pop(processorKey, None)
		_state._playerUtteranceQualities.pop(processorKey, None)


def _clearIdlePlayerUtterancePitches() -> None:
	with _state._playerProcessorsLock:
		for processorKey in list(_state._playerUtterancePitches):
			processor = _state._playerProcessors.get(processorKey)
			if processor is None or processor.isIdleForPitchChange():
				_state._playerUtterancePitches.pop(processorKey, None)
				_state._playerUtteranceQualities.pop(processorKey, None)
		for processorKey in list(_state._playerUtteranceQualities):
			if processorKey not in _state._playerUtterancePitches:
				_state._playerUtteranceQualities.pop(processorKey, None)


def _logDeferredPitchOnce(synthName: str, activePitch: int, pendingPitch: int) -> None:
	key = (synthName, activePitch, pendingPitch)
	if key in _state._deferredPitchLogKeys and not _configuration._isDebugLoggingEnabled():
		return
	_state._deferredPitchLogKeys.add(key)
	log.info(
		"globalSonicPitch: deferring Sonic pitch change until next utterance; "
		f"synth={synthName or 'unknown'}; activePitch={activePitch}; pendingPitch={pendingPitch}",
	)


def _logDeferredQualityOnce(synthName: str, activeQuality: int, pendingQuality: int) -> None:
	key = ("quality", synthName, activeQuality, pendingQuality)
	if key in _state._deferredPitchLogKeys and not _configuration._isDebugLoggingEnabled():
		return
	_state._deferredPitchLogKeys.add(key)
	log.info(
		"globalSonicPitch: deferring Sonic quality change until next utterance; "
		f"synth={synthName or 'unknown'}; activeQuality={activeQuality} ({_configuration._getQualityLabel(activeQuality)}); "
		f"pendingQuality={pendingQuality} ({_configuration._getQualityLabel(pendingQuality)})",
	)


def _getOrCreatePlayerProcessor(
	player: nvwave.WavePlayer,
	channels: int,
	sampleRate: int,
	pitchPercent: int,
	quality: int,
) -> tuple[_native._SonicStreamProcessor | None, bytes]:
	retiredProcessor = None
	with _state._playerProcessorsLock:
		processorKey = _getPlayerProcessorKey(player)
		processor = _state._playerProcessors.get(processorKey)
		if processor is not None:
			if (
				processor.formatMatches(channels, sampleRate, quality)
				and processor.pitchPercent == _configuration._clampPitch(pitchPercent)
			):
				return processor, b""
			retiredProcessor = _state._playerProcessors.pop(processorKey, None)
			log.info(
				"globalSonicPitch: recreating Sonic processor for new parameters; "
				f"pitch={_configuration._clampPitch(pitchPercent)}; quality={_configuration._clampQuality(quality)} ({_configuration._getQualityLabel(quality)})",
			)
		sonic = _native._getSonicModule()
		if sonic is None:
			return None, b""
		processor = _native._SonicStreamProcessor(sonic, channels, sampleRate, pitchPercent, quality)
		_state._playerProcessors[processorKey] = processor
	tail = _finishProcessorSafely(retiredProcessor)
	if retiredProcessor is not None:
		retiredProcessor.completePendingOnDone()
	return processor, tail


def _processPcm16Block(
	player: nvwave.WavePlayer,
	raw: bytes,
	channels: int,
	sampleRate: int,
	pitchPercent: int,
	quality: int,
) -> tuple[bytes, _native._SonicStreamProcessor] | None:
	frameSize = channels * 2
	if len(raw) < frameSize or len(raw) % frameSize:
		return None
	processor, tail = _getOrCreatePlayerProcessor(player, channels, sampleRate, pitchPercent, quality)
	if processor is None:
		return None
	processed = processor.process(raw)
	return (tail + processed, processor)


def _logProcessedOnce(
	synthName: str,
	channels: int,
	sampleRate: int,
	pitch: int,
	quality: int,
	inSize: int,
	outSize: int,
) -> None:
	key = (synthName, channels, sampleRate, pitch, quality)
	if key in _state._processingLogKeys and not _configuration._isDebugLoggingEnabled():
		return
	_state._processingLogKeys.add(key)
	log.info(
		"globalSonicPitch: processed speech audio; "
		f"synth={synthName or 'unknown'}; pitch={pitch}; "
		f"quality={quality} ({_configuration._getQualityLabel(quality)}); "
		f"channels={channels}; sampleRate={sampleRate}; bytes={inSize}->{outSize}",
	)


def _getOriginalWavePlayerMethod(methodName: str) -> Callable[..., Any]:
	originalMethod = _state._originalWavePlayerMethods.get(methodName)
	if originalMethod is None:
		raise RuntimeError(f"globalSonicPitch: original WavePlayer method is unavailable: {methodName}")
	return originalMethod


def _patchedFeed(self, data, size=None, onDone=None):
	originalFeed = _getOriginalWavePlayerMethod("feed")
	if callable(size) and onDone is None:
		onDone = size
		size = None
	raw = _getRawBytes(data, size)
	try:
		if raw is not None and len(raw) == 0:
			tail, pendingOnDone = _finishPlayerProcessor(self)
			if tail:
				originalFeed(self, tail, len(tail), pendingOnDone)
			elif pendingOnDone is not None:
				originalFeed(self, None, 0, pendingOnDone)
			_clearPlayerUtterancePitch(self)
			return originalFeed(self, data, size, onDone)
		processingContext = _getProcessingContext(self, len(raw)) if raw is not None else None
		if raw is not None and processingContext is not None:
			synthName, pitch, quality = processingContext
			waveFormat = _getWaveFormat(self)
			if waveFormat is not None:
				channels, sampleRate, bitsPerSample = waveFormat
				if bitsPerSample == 16:
					processedResult = _processPcm16Block(self, raw, channels, sampleRate, pitch, quality)
					if processedResult is not None:
						processed, processor = processedResult
						_logProcessedOnce(
							synthName,
							channels,
							sampleRate,
							pitch,
							processor.appliedQuality,
							len(raw),
							len(processed),
						)
						if processed:
							return originalFeed(self, processed, len(processed), processor.takeOnDone(onDone))
						if onDone is not None:
							processor.deferOnDone(onDone)
						return None
				elif _configuration._isDebugLoggingEnabled():
					log.debug(f"globalSonicPitch: bypassing non-16-bit audio: {bitsPerSample}")
		elif raw is not None:
			_resetPlayerProcessor(self)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to process WavePlayer feed; bypassing", exc_info=True)
		_resetPlayerProcessor(self)
	return originalFeed(self, data, size, onDone)


def _feedProcessorTail(player: nvwave.WavePlayer) -> None:
	originalFeed = _getOriginalWavePlayerMethod("feed")
	try:
		tail, onDone = _finishPlayerProcessor(player)
		if tail:
			originalFeed(player, tail, len(tail), onDone)
		elif onDone is not None:
			originalFeed(player, None, 0, onDone)
	except Exception:
		log.debugWarning("globalSonicPitch: failed to flush Sonic stream tail", exc_info=True)
		_resetPlayerProcessor(player)
	finally:
		_clearPlayerUtterancePitch(player)


def _patchedIdle(self, *args, **kwargs):
	_feedProcessorTail(self)
	originalIdle = _getOriginalWavePlayerMethod("idle")
	return originalIdle(self, *args, **kwargs)


def _patchedStop(self, *args, **kwargs):
	_resetPlayerProcessor(self)
	_clearPlayerUtterancePitch(self)
	originalStop = _getOriginalWavePlayerMethod("stop")
	return originalStop(self, *args, **kwargs)


def _patchedClose(self, *args, **kwargs):
	_resetPlayerProcessor(self)
	_clearPlayerUtterancePitch(self)
	originalClose = _getOriginalWavePlayerMethod("close")
	return originalClose(self, *args, **kwargs)


def installWavePlayerHook() -> None:
	wavePlayerClass = getattr(nvwave, "WavePlayer", None)
	if not inspect.isclass(wavePlayerClass):
		log.debugWarning(
			"globalSonicPitch: WavePlayer hook not installed because nvwave.WavePlayer is not a class",
		)
		return
	if getattr(wavePlayerClass, _state._FEED_PATCHED_ATTR, False):
		_state._originalWavePlayerClass = wavePlayerClass
		_state._originalWavePlayerMethods = {
			methodName: getattr(wavePlayerClass, attrName)
			for methodName, attrName in (
				("feed", _state._ORIGINAL_FEED_ATTR),
				("idle", _state._ORIGINAL_IDLE_ATTR),
				("stop", _state._ORIGINAL_STOP_ATTR),
				("close", _state._ORIGINAL_CLOSE_ATTR),
			)
			if callable(getattr(wavePlayerClass, attrName, None))
		}
		return
	originalFeed = getattr(wavePlayerClass, "feed", None)
	if not callable(originalFeed):
		log.debugWarning("globalSonicPitch: WavePlayer hook not installed because feed is unavailable")
		return
	_state._originalWavePlayerClass = wavePlayerClass
	_state._originalWavePlayerMethods = {"feed": originalFeed}
	setattr(wavePlayerClass, _state._ORIGINAL_FEED_ATTR, originalFeed)
	wavePlayerClass.feed = _patchedFeed
	for methodName, methodAttr, patchedMethod in (
		("idle", _state._ORIGINAL_IDLE_ATTR, _patchedIdle),
		("stop", _state._ORIGINAL_STOP_ATTR, _patchedStop),
		("close", _state._ORIGINAL_CLOSE_ATTR, _patchedClose),
	):
		originalMethod = getattr(wavePlayerClass, methodName, None)
		if not callable(originalMethod):
			continue
		_state._originalWavePlayerMethods[methodName] = originalMethod
		setattr(wavePlayerClass, methodAttr, originalMethod)
		setattr(wavePlayerClass, methodName, patchedMethod)
	setattr(wavePlayerClass, _state._FEED_PATCHED_ATTR, True)
	log.info("globalSonicPitch: installed WavePlayer speech feed hook")


def uninstallWavePlayerHook() -> None:
	wavePlayerClass = _state._originalWavePlayerClass
	if wavePlayerClass is None:
		currentWavePlayerClass = getattr(nvwave, "WavePlayer", None)
		if inspect.isclass(currentWavePlayerClass) and getattr(currentWavePlayerClass, _state._FEED_PATCHED_ATTR, False):
			wavePlayerClass = currentWavePlayerClass
	if wavePlayerClass is None or not getattr(wavePlayerClass, _state._FEED_PATCHED_ATTR, False):
		return
	for methodName, methodAttr, patchedMethod in (
		("feed", _state._ORIGINAL_FEED_ATTR, _patchedFeed),
		("idle", _state._ORIGINAL_IDLE_ATTR, _patchedIdle),
		("stop", _state._ORIGINAL_STOP_ATTR, _patchedStop),
		("close", _state._ORIGINAL_CLOSE_ATTR, _patchedClose),
	):
		originalMethod = _state._originalWavePlayerMethods.get(methodName)
		if originalMethod is None:
			originalMethod = getattr(wavePlayerClass, methodAttr, None)
		if originalMethod is not None and getattr(wavePlayerClass, methodName, None) is patchedMethod:
			setattr(wavePlayerClass, methodName, originalMethod)
	try:
		delattr(wavePlayerClass, _state._ORIGINAL_FEED_ATTR)
	except Exception:
		pass
	for attr in (_state._ORIGINAL_IDLE_ATTR, _state._ORIGINAL_STOP_ATTR, _state._ORIGINAL_CLOSE_ATTR):
		try:
			delattr(wavePlayerClass, attr)
		except Exception:
			pass
	_resetAllPlayerProcessors()
	setattr(wavePlayerClass, _state._FEED_PATCHED_ATTR, False)
	_state._originalWavePlayerClass = None
	_state._originalWavePlayerMethods = {}
	log.info("globalSonicPitch: removed WavePlayer speech feed hook")
