"""Small NVDA/WavePlayer doubles; no native DLL or Windows audio is executed."""
from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
import importlib
import importlib.util
import inspect
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "globalPlugins.globalSonicPitch"


class Environment:
    def owner(self, name):
        if hasattr(self.plugin, name):
            return self.plugin
        for component in ("state", "configuration", "synths", "host", "dialogs", "native", "audio", "settings_panel"):
            module = sys.modules.get(f"{PLUGIN_NAME}.{component}")
            if module is not None and name in vars(module):
                return module
        raise AttributeError(name)

    def get(self, name):
        return getattr(self.owner(name), name)

    def replace(self, name, value):
        return patch.object(self.owner(name), name, value)

    def drain(self):
        for _ in range(100):
            if not self.pending:
                return
            callback, args, kwargs = self.pending.pop(0)
            callback(*args, **kwargs)
        raise AssertionError("Unexpected unbounded CallAfter scheduling")

    def load(self):
        for name in list(sys.modules):
            if name == PLUGIN_NAME or name.startswith(PLUGIN_NAME + "."):
                del sys.modules[name]
        legacy = os.environ.get("SONICPITCH_BASELINE")
        if legacy:
            spec = importlib.util.spec_from_file_location(PLUGIN_NAME, legacy)
            self.plugin = importlib.util.module_from_spec(spec)
            sys.modules[PLUGIN_NAME] = self.plugin
            spec.loader.exec_module(self.plugin)
        else:
            self.plugin = importlib.import_module(PLUGIN_NAME)


@contextmanager
def nvda_environment():
    env = Environment()
    env.pending = []
    env.messages = []
    env.log_entries = []
    env.streams = []
    modules = {}

    def module(name, **attrs):
        result = ModuleType(name)
        result.__dict__.update(attrs)
        modules[name] = result
        return result

    class Config(dict):
        spec = {}
        saves = 0

        def save(self):
            self.saves += 1

    env.conf = Config(globalSonicPitch={
        "enabled": False, "pitch": 50, "pitchBySynth": "{}", "extendedPitchRange": False,
        "sonicQuality": 0, "debugLogging": False,
    })
    module("config", conf=env.conf)

    class Synth:
        name = "testSynth"
        supportedSettings = ()
        pitch = 50

        def __init__(self):
            self._voice = "first"
            self._variant = "base"

        @property
        def voice(self):
            return self._voice

        @voice.setter
        def voice(self, value):
            self._voice = value

        @property
        def variant(self):
            return self._variant

        @variant.setter
        def variant(self, value):
            self._variant = value

    env.synth = Synth()

    def set_synth(name, isFallback=False):
        env.synth.name = name
        return True

    env.handler = module("synthDriverHandler", getSynth=lambda: env.synth, setSynth=set_synth)
    env.Synth = Synth

    class AudioPurpose(Enum):
        SPEECH = 1
        OTHER = 2

    class WavePlayer:
        def __init__(self, bits=16, purpose=AudioPurpose.SPEECH):
            self._purpose = purpose
            self._format = SimpleNamespace(nChannels=1, nSamplesPerSec=1000, wBitsPerSample=bits)
            self.blocks = []
            self.operations = []

        def feed(self, data, size=None, onDone=None):
            raw = bytes(data) if data is not None else b""
            self.blocks.append(raw if size is None else raw[:size])
            if onDone:
                onDone()

        def idle(self):
            self.operations.append("idle")

        def stop(self):
            self.operations.append("stop")

        def close(self):
            self.operations.append("close")

    env.wave = module("nvwave", WavePlayer=WavePlayer, AudioPurpose=AudioPurpose)
    env.WavePlayer = WavePlayer

    class Stream:
        def __init__(self, sampleRate, channels):
            self.channels = channels
            self.data = b""
            self.pitch = 1.0
            self.quality = 0
            self.flushes = 0
            self.fail = False
            env.streams.append(self)

        @property
        def samplesAvailable(self):
            return len(self.data) // (self.channels * 2)

        def writeShort(self, samples, count):
            if self.fail:
                raise RuntimeError("simulated native write failure")
            self.data += bytes(samples)

        def readShort(self):
            result, self.data = self.data, b""
            return result

        def flush(self):
            self.flushes += 1

    env.sonic = SimpleNamespace(SonicStream=Stream)
    module("ui", message=env.messages.append)
    module("wx", CallAfter=lambda callback, *args, **kwargs: env.pending.append((callback, args, kwargs)),
           EVT_WINDOW_DESTROY=1)

    class SettingsPanel:
        def Bind(self, *args):
            pass

        def IsBeingDeleted(self):
            return False

    class AutoSettingsMixin:
        def refreshGui(self):
            return "refreshed"

    class VoiceSettingsPanel(SettingsPanel, AutoSettingsMixin):
        def makeSettings(self, *args):
            return "created"

        def onSave(self):
            return "saved"

        def onDiscard(self):
            return "discarded"

        def updateDriverSettings(self, **kwargs):
            pass

    class SettingsDialog:
        _instances = {}
        DialogState = SimpleNamespace(DESTROYED="destroyed", OPEN="open")

        def _setInstanceDestroyedState(self):
            self._instances[self] = self.DialogState.DESTROYED

    env.dialogs = module("gui.settingsDialogs", SettingsPanel=SettingsPanel,
        NVDASettingsDialog=SimpleNamespace(categoryClasses=[]), VoiceSettingsPanel=VoiceSettingsPanel,
        SettingsDialog=SettingsDialog, AutoSettingsMixin=AutoSettingsMixin, setSynth=set_synth)
    helper = module("gui.guiHelper")
    module("gui", settingsDialogs=env.dialogs, guiHelper=helper)
    module("globalVars", settingsRing=SimpleNamespace(updateSupportedSettings=lambda: None))

    class GlobalPlugin:
        def __init__(self, *args, **kwargs):
            pass

        def terminate(self):
            pass

    module("globalPluginHandler", GlobalPlugin=GlobalPlugin)

    def script(**kwargs):
        def decorate(function):
            function.__doc__ = kwargs.get("description")
            function.category = kwargs.get("category")
            return function
        return decorate

    module("scriptHandler", script=script)

    def init_translation():
        inspect.currentframe().f_back.f_globals["_"] = lambda message: "translated:" + message

    module("addonHandler", initTranslation=init_translation)
    module("logHandler", log=SimpleNamespace(**{
        method: (lambda *args, _method=method, **kwargs: env.log_entries.append((_method, args)))
        for method in ("debug", "debugWarning", "info", "error", "exception")
    }))

    class NumericDriverSetting:
        def __init__(self, setting_id, label, *args, **kwargs):
            self.id = setting_id
            self.label = label

    module("autoSettingsUtils", __path__=[])
    module("autoSettingsUtils.driverSetting", NumericDriverSetting=NumericDriverSetting)
    synth_drivers = module("synthDrivers", __path__=[])
    env.host_classes = []
    for name in ("sapi4_32", "sapi5_32"):
        driver = type("SynthDriver", (), {"synthDriver32Path": f"original/{name}"})
        child = module(f"synthDrivers.{name}", SynthDriver=driver)
        setattr(synth_drivers, name, child)
        env.host_classes.append(driver)
    module("globalPlugins", __path__=[str(ROOT / "addon/globalPlugins")])

    existing = {name: value for name, value in sys.modules.items() if name == PLUGIN_NAME or name.startswith(PLUGIN_NAME + ".")}
    for name in existing:
        del sys.modules[name]
    try:
        with patch.dict(sys.modules, modules):
            env.load()
            yield env
    finally:
        for name in list(sys.modules):
            if name == PLUGIN_NAME or name.startswith(PLUGIN_NAME + "."):
                del sys.modules[name]
        sys.modules.update(existing)
