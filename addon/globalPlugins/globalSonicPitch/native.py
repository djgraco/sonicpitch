"""Sonic loading, stream lifetime and PCM stream processor."""

from __future__ import annotations

from ._nvda import (
	Any,
	Callable,
	ctypes,
	log,
	os,
	threading,
)
from . import configuration as _configuration
from . import state as _state


class _SonicStreamP(ctypes.c_void_p):
	pass


class _BundledSonicModule:
	def __init__(self, sonicLib: ctypes.CDLL, dllPath: str):
		self.sonicLib = sonicLib
		self.dllPath = dllPath
		self.isBundled = True


def _configureSonicLibrary(sonicLib: ctypes.CDLL) -> None:
	sonicLib.sonicCreateStream.restype = _SonicStreamP
	sonicLib.sonicCreateStream.argtypes = [ctypes.c_int, ctypes.c_int]
	sonicLib.sonicDestroyStream.restype = None
	sonicLib.sonicDestroyStream.argtypes = [_SonicStreamP]
	sonicLib.sonicWriteFloatToStream.restype = ctypes.c_int
	sonicLib.sonicWriteFloatToStream.argtypes = [_SonicStreamP, ctypes.c_void_p, ctypes.c_int]
	sonicLib.sonicWriteShortToStream.restype = ctypes.c_int
	sonicLib.sonicWriteShortToStream.argtypes = [_SonicStreamP, ctypes.c_void_p, ctypes.c_int]
	sonicLib.sonicWriteUnsignedCharToStream.restype = ctypes.c_int
	sonicLib.sonicWriteUnsignedCharToStream.argtypes = [_SonicStreamP, ctypes.c_void_p, ctypes.c_int]
	sonicLib.sonicReadFloatFromStream.restype = ctypes.c_int
	sonicLib.sonicReadFloatFromStream.argtypes = [_SonicStreamP, ctypes.c_void_p, ctypes.c_int]
	sonicLib.sonicReadShortFromStream.restype = ctypes.c_int
	sonicLib.sonicReadShortFromStream.argtypes = [_SonicStreamP, ctypes.c_void_p, ctypes.c_int]
	sonicLib.sonicReadUnsignedCharFromStream.restype = ctypes.c_int
	sonicLib.sonicReadUnsignedCharFromStream.argtypes = [_SonicStreamP, ctypes.c_void_p, ctypes.c_int]
	sonicLib.sonicFlushStream.restype = ctypes.c_int
	sonicLib.sonicFlushStream.argtypes = [_SonicStreamP]
	sonicLib.sonicSamplesAvailable.restype = ctypes.c_int
	sonicLib.sonicSamplesAvailable.argtypes = [_SonicStreamP]
	sonicLib.sonicGetSpeed.restype = ctypes.c_float
	sonicLib.sonicGetSpeed.argtypes = [_SonicStreamP]
	sonicLib.sonicSetSpeed.restype = None
	sonicLib.sonicSetSpeed.argtypes = [_SonicStreamP, ctypes.c_float]
	sonicLib.sonicGetPitch.restype = ctypes.c_float
	sonicLib.sonicGetPitch.argtypes = [_SonicStreamP]
	sonicLib.sonicSetPitch.restype = None
	sonicLib.sonicSetPitch.argtypes = [_SonicStreamP, ctypes.c_float]
	sonicLib.sonicGetRate.restype = ctypes.c_float
	sonicLib.sonicGetRate.argtypes = [_SonicStreamP]
	sonicLib.sonicSetRate.restype = None
	sonicLib.sonicSetRate.argtypes = [_SonicStreamP, ctypes.c_float]
	sonicLib.sonicGetVolume.restype = ctypes.c_float
	sonicLib.sonicGetVolume.argtypes = [_SonicStreamP]
	sonicLib.sonicSetVolume.restype = None
	sonicLib.sonicSetVolume.argtypes = [_SonicStreamP, ctypes.c_float]
	sonicLib.sonicGetQuality.restype = ctypes.c_int
	sonicLib.sonicGetQuality.argtypes = [_SonicStreamP]
	sonicLib.sonicSetQuality.restype = None
	sonicLib.sonicSetQuality.argtypes = [_SonicStreamP, ctypes.c_int]
	sonicLib.sonicGetSampleRate.restype = ctypes.c_int
	sonicLib.sonicGetSampleRate.argtypes = [_SonicStreamP]
	sonicLib.sonicSetSampleRate.restype = None
	sonicLib.sonicSetSampleRate.argtypes = [_SonicStreamP, ctypes.c_int]
	sonicLib.sonicGetNumChannels.restype = ctypes.c_int
	sonicLib.sonicGetNumChannels.argtypes = [_SonicStreamP]
	sonicLib.sonicSetNumChannels.restype = None
	sonicLib.sonicSetNumChannels.argtypes = [_SonicStreamP, ctypes.c_int]


def _getBundledSonicPath() -> str:
	dllName = _state._BUNDLED_SONIC_32_DLL if _is32BitProcess() else _state._BUNDLED_SONIC_64_DLL
	return os.path.join(os.path.dirname(os.path.dirname(__file__)), _state._BUNDLED_SONIC_DIR, dllName)


def _loadBundledSonicModule() -> _BundledSonicModule | None:
	dllPath = _getBundledSonicPath()
	if not os.path.isfile(dllPath):
		return None
	sonicLib = ctypes.CDLL(dllPath)
	_configureSonicLibrary(sonicLib)
	log.info(f"globalSonicPitch: loaded bundled Sonic library; path={dllPath}")
	return _BundledSonicModule(sonicLib, dllPath)


def _getSonicModule():
	if _state._sonicModule is not None:
		return _state._sonicModule
	bundledError = None
	try:
		_state._sonicModule = _loadBundledSonicModule()
		if _state._sonicModule is not None:
			_state._sonicUnavailableReason = None
			return _state._sonicModule
	except Exception as exc:
		bundledError = f"{type(exc).__name__}: {exc}"
		if _configuration._isDebugLoggingEnabled():
			log.debugWarning("globalSonicPitch: bundled Sonic is unavailable", exc_info=True)
	try:
		from synthDrivers import _sonic

		_sonic.initialize()
		_state._sonicModule = _sonic
		_state._sonicUnavailableReason = None
	except Exception as exc:
		nvdaError = f"{type(exc).__name__}: {exc}"
		if bundledError:
			_state._sonicUnavailableReason = f"bundled Sonic: {bundledError}; NVDA Sonic: {nvdaError}"
		else:
			_state._sonicUnavailableReason = f"NVDA Sonic: {nvdaError}"
		if _configuration._isDebugLoggingEnabled():
			log.debugWarning("globalSonicPitch: Sonic is unavailable", exc_info=True)
		return None
	return _state._sonicModule


def _ctypesArrayToBytes(value: Any) -> bytes:
	try:
		if not value:
			return b""
		return ctypes.string_at(ctypes.addressof(value), ctypes.sizeof(value))
	except Exception:
		return bytes(value)


def _is32BitProcess() -> bool:
	return ctypes.sizeof(ctypes.c_void_p) == 4


class _NoDestroySonicStream:
	"""Sonic stream wrapper that avoids unstable native destruction in 32-bit NVDA."""

	def __init__(self, sonicModule: Any, sampleRate: int, channels: int):
		self._sonicModule = sonicModule
		self.channels = channels
		self.stream = sonicModule.sonicLib.sonicCreateStream(sampleRate, channels)
		if not self.stream:
			raise MemoryError()

	def writeShort(self, data: Any, numSamples: int) -> None:
		if not self._sonicModule.sonicLib.sonicWriteShortToStream(self.stream, data, numSamples):
			raise MemoryError()

	def readShort(self) -> Any:
		samples = self.samplesAvailable
		buffer = (ctypes.c_short * (samples * self.channels))()
		self._sonicModule.sonicLib.sonicReadShortFromStream(self.stream, buffer, samples)
		return buffer

	def flush(self) -> None:
		if not self._sonicModule.sonicLib.sonicFlushStream(self.stream):
			raise MemoryError()

	@property
	def samplesAvailable(self) -> int:
		return self._sonicModule.sonicLib.sonicSamplesAvailable(self.stream)

	@property
	def pitch(self) -> float:
		return self._sonicModule.sonicLib.sonicGetPitch(self.stream)

	@pitch.setter
	def pitch(self, value: float) -> None:
		self._sonicModule.sonicLib.sonicSetPitch(self.stream, value)

	@property
	def quality(self) -> int:
		return self._sonicModule.sonicLib.sonicGetQuality(self.stream)

	@quality.setter
	def quality(self, value: int) -> None:
		self._sonicModule.sonicLib.sonicSetQuality(self.stream, _configuration._clampQuality(value))


class _DestroySonicStream(_NoDestroySonicStream):
	def __del__(self):
		stream = getattr(self, "stream", None)
		if not stream:
			return
		try:
			self._sonicModule.sonicLib.sonicDestroyStream(stream)
		except Exception:
			pass
		self.stream = None


def _createSonicStream(sonicModule: Any, sampleRate: int, channels: int) -> Any:
	if _is32BitProcess():
		if not _state._noDestroySonicStreamLogged:
			_state._noDestroySonicStreamLogged = True
			log.info("globalSonicPitch: using no-destroy Sonic stream wrapper for 32-bit NVDA stability")
		return _NoDestroySonicStream(sonicModule, sampleRate, channels)
	if getattr(sonicModule, "isBundled", False):
		return _DestroySonicStream(sonicModule, sampleRate, channels)
	return sonicModule.SonicStream(sampleRate, channels)


def _getStreamSonicQuality(stream: Any, fallback: int) -> int:
	try:
		return _configuration._clampQuality(stream.quality)
	except Exception:
		return _configuration._clampQuality(fallback)


def _applySonicQualityToStream(stream: Any, quality: int, source: str, sampleRate: int, channels: int) -> int:
	requestedQuality = _configuration._clampQuality(quality)
	try:
		stream.quality = requestedQuality
	except Exception:
		appliedQuality = 0
		key = (source, "fallback", requestedQuality)
		if key not in _state._qualityLogKeys:
			_state._qualityLogKeys.add(key)
			log.debugWarning(
				"globalSonicPitch: failed to set Sonic quality; using stream default fast mode; "
				f"source={source}; requestedQuality={requestedQuality}; appliedQuality={appliedQuality}",
				exc_info=True,
			)
		return appliedQuality
	appliedQuality = _getStreamSonicQuality(stream, requestedQuality)
	key = (source, sampleRate, channels, requestedQuality, appliedQuality)
	if key not in _state._qualityLogKeys or _configuration._isDebugLoggingEnabled():
		_state._qualityLogKeys.add(key)
		log.info(
			"globalSonicPitch: applied Sonic quality to new stream; "
			f"source={source}; requestedQuality={requestedQuality}; "
			f"appliedQuality={appliedQuality} ({_configuration._getQualityLabel(appliedQuality)}); "
			f"sampleRate={sampleRate}; channels={channels}",
		)
	return appliedQuality


class _SonicStreamProcessor:
	def __init__(self, sonicModule: Any, channels: int, sampleRate: int, pitchPercent: int, quality: int):
		self.channels = channels
		self.sampleRate = sampleRate
		self.stream = _createSonicStream(sonicModule, sampleRate, channels)
		self.pitchPercent = _configuration._clampPitch(pitchPercent)
		self.requestedQuality = _configuration._clampQuality(quality)
		self.appliedQuality = _applySonicQualityToStream(
			self.stream,
			self.requestedQuality,
			"main",
			sampleRate,
			channels,
		)
		self.stream.pitch = _configuration._pitchPercentToSonicRatio(self.pitchPercent)
		self.isFirstAudioChunk = True
		self.isActive = False
		self._pendingInputFrames = 0
		self._pendingOnDoneCallbacks: list[Callable[..., Any]] = []
		self._lock = threading.RLock()

	def formatMatches(self, channels: int, sampleRate: int, quality: int) -> bool:
		return (
			self.channels == channels
			and self.sampleRate == sampleRate
			and self.requestedQuality == _configuration._clampQuality(quality)
		)

	def isIdleForPitchChange(self) -> bool:
		with self._lock:
			if self.isActive:
				return False
			try:
				return self.isFirstAudioChunk and self.stream.samplesAvailable <= 0
			except Exception:
				return False

	def _readAvailable(self) -> bytes:
		if self.stream.samplesAvailable <= 0:
			return b""
		return _ctypesArrayToBytes(self.stream.readShort())

	def deferOnDone(self, callback: Callable[..., Any] | None) -> None:
		if not callable(callback):
			return
		with self._lock:
			self._pendingOnDoneCallbacks.append(callback)

	def takeOnDone(self, callback: Callable[..., Any] | None = None) -> Callable[..., None] | None:
		with self._lock:
			callbacks = self._pendingOnDoneCallbacks
			self._pendingOnDoneCallbacks = []
		if callable(callback):
			callbacks.append(callback)
		if not callbacks:
			return None

		def _onDone(*args, **kwargs):
			for pendingCallback in callbacks:
				try:
					pendingCallback()
				except Exception:
					log.debugWarning("globalSonicPitch: failed to run deferred WavePlayer callback", exc_info=True)

		return _onDone

	def completePendingOnDone(self) -> None:
		onDone = self.takeOnDone()
		if onDone is not None:
			onDone()

	def process(self, raw: bytes, flush: bool = False) -> bytes:
		with self._lock:
			frameSize = self.channels * 2
			if raw:
				self.isActive = True
				frameCount = len(raw) // frameSize
				self._pendingInputFrames += frameCount
				sampleCount = frameCount * self.channels
				inputSamples = (ctypes.c_short * sampleCount).from_buffer_copy(raw)
				self.stream.writeShort(inputSamples, frameCount)
			if flush:
				self.stream.flush()
				self.isFirstAudioChunk = False
			elif (
				self.isFirstAudioChunk
				and self.stream.samplesAvailable < self.sampleRate * _state._FIRST_AUDIO_CHUNK_MIN_DURATION_MS // 1000
				and self._pendingInputFrames > self.sampleRate * _state._SHORT_AUDIO_CHUNK_MAX_DURATION_MS // 1000
			):
				return b""
			self.isFirstAudioChunk = False
			processed = self._readAvailable()
			if processed or flush:
				self._pendingInputFrames = 0
			return processed

	def finish(self) -> bytes:
		try:
			return self.process(b"", flush=True)
		finally:
			with self._lock:
				self.isFirstAudioChunk = True
				self.isActive = False
				self._pendingInputFrames = 0
