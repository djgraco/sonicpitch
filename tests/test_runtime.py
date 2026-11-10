"""Regression tests for module boundaries with explicit NVDA/audio doubles."""
import inspect
import json
import os
from pathlib import Path
import pkgutil
from types import SimpleNamespace
import unittest

from nvda_stub import nvda_environment, PLUGIN_NAME


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.context = nvda_environment()
        self.env = self.context.__enter__()
        self.addCleanup(self.context.__exit__, None, None, None)

    def start(self, enabled=True):
        self.env.conf["globalSonicPitch"]["enabled"] = enabled
        plugin = self.env.plugin.GlobalPlugin()
        self.addCleanup(plugin.terminate)
        return plugin

    def test_plugin_identity_and_translated_gestures(self):
        plugin_class = self.env.plugin.GlobalPlugin
        self.assertEqual(plugin_class.__module__, PLUGIN_NAME)
        scripts = [name for name in vars(plugin_class) if name.startswith("script_")]
        self.assertEqual(len(scripts), 6)
        self.assertTrue(plugin_class.script_toggleGlobalSonicPitch.__doc__.startswith("translated:"))
        self.assertEqual(self.env.get("GlobalSonicPitchSettingsPanel").title, "translated:Global Sonic Pitch")
        if not os.environ.get("SONICPITCH_BASELINE"):
            self.assertIn("globalSonicPitch", [name for _, name, _ in pkgutil.iter_modules([str(Path(self.env.plugin.__file__).parent.parent)])])

    def test_resource_paths_reach_existing_dlls_and_host_drivers(self):
        for is_32, filename in [(False, "sonic64.dll"), (True, "sonic32.dll")]:
            with self.env.replace("_is32BitProcess", lambda: is_32):
                path = Path(self.env.get("_getBundledSonicPath")())
                self.assertEqual(path.name, filename)
                self.assertTrue(path.is_file())
        path = Path(self.env.get("_getSapi32HostDriverPath")())
        self.assertTrue((path / "sapi4.py").is_file())
        self.assertTrue((path / "sapi5.py").is_file())

    def test_lifecycle_restores_hooks_settings_and_sapi_paths(self):
        cls = self.env.WavePlayer
        original = [getattr(cls, method) for method in ("feed", "idle", "stop", "close")]
        original_set_synth = self.env.handler.setSynth
        original_voice = self.env.dialogs.VoiceSettingsPanel.onDiscard
        plugin = self.env.plugin.GlobalPlugin()
        self.assertNotEqual(cls.feed, original[0])
        self.env.get("_setGlobalEnabled")(True)
        self.assertTrue(hasattr(self.env.synth, "sonicPitch"))
        self.assertEqual(self.env.synth.pitch, 50)
        self.assertEqual(len(self.env.dialogs.NVDASettingsDialog.categoryClasses), 1)
        plugin.terminate()
        self.assertEqual(original, [getattr(cls, method) for method in ("feed", "idle", "stop", "close")])
        self.assertIs(self.env.handler.setSynth, original_set_synth)
        self.assertIs(self.env.dialogs.VoiceSettingsPanel.onDiscard, original_voice)
        self.assertFalse(hasattr(self.env.synth, "sonicPitch"))
        self.assertEqual(self.env.dialogs.NVDASettingsDialog.categoryClasses, [])
        for name, driver in zip(("sapi4_32", "sapi5_32"), self.env.host_classes):
            self.assertEqual(driver.synthDriver32Path, f"original/{name}")

    def test_distinct_voices_and_variants_keep_values(self):
        self.start()
        set_pitch = self.env.get("_setCurrentSynthSonicPitch")
        get_pitch = self.env.get("_getSonicPitchForSynth")
        set_pitch(65)
        self.env.synth.voice = "second"
        self.assertEqual(get_pitch(), 50)
        set_pitch(35)
        self.env.synth.variant = "alternate"
        self.assertEqual(get_pitch(), 50)
        set_pitch(75)
        self.env.synth.variant = "base"
        self.assertEqual(get_pitch(), 35)
        self.env.synth.voice = "first"
        self.assertEqual(get_pitch(), 65)
        self.assertEqual(len(json.loads(self.env.conf["globalSonicPitch"]["pitchBySynth"])), 3)

    def test_unload_and_reimport_keep_saved_values_with_fresh_runtime_state(self):
        plugin = self.start()
        self.env.get("_setCurrentSynthSonicPitch")(65)
        previous_sessions = self.env.get("_voiceDialogSessions")
        plugin.terminate()
        self.env.drain()
        self.env.load()
        self.start()
        self.assertEqual(self.env.get("_getSonicPitchForSynth")(), 65)
        self.assertIsNot(self.env.get("_voiceDialogSessions"), previous_sessions)
        self.assertFalse(self.env.get("_voiceDialogSessions"))
        self.assertEqual(len(self.env.dialogs.NVDASettingsDialog.categoryClasses), 1)

    def test_voice_dialog_discard_restores_all_touched_voices(self):
        self.start()
        panel = self.env.dialogs.VoiceSettingsPanel()
        panel.makeSettings(None)
        self.env.get("_setCurrentSynthSonicPitch")(65)
        self.env.synth.voice = "second"
        self.env.get("_setCurrentSynthSonicPitch")(35)
        self.assertEqual(self.env.get("_getSonicPitchForSynth")(), 35)
        self.assertEqual(json.loads(self.env.conf["globalSonicPitch"]["pitchBySynth"]), {})
        panel.onDiscard()
        self.assertEqual(self.env.get("_getSonicPitchForSynth")(), 50)
        self.env.synth.voice = "first"
        self.assertEqual(self.env.get("_getSonicPitchForSynth")(), 50)
        self.assertFalse(self.env.get("_voiceDialogSessions"))
        self.env.drain()

    def test_voice_dialog_apply_commits_preview(self):
        self.start()
        panel = self.env.dialogs.VoiceSettingsPanel()
        panel.makeSettings(None)
        self.env.get("_setCurrentSynthSonicPitch")(68)
        panel.onSave()
        self.assertEqual(self.env.get("_getSonicPitchForSynth")(), 68)
        self.assertIn(68, json.loads(self.env.conf["globalSonicPitch"]["pitchBySynth"]).values())

    def test_dynamic_read_only_settings_stay_dynamic(self):
        class DynamicSynth(self.env.Synth):
            @property
            def supportedSettings(self):
                return (SimpleNamespace(id="dynamic-" + self.voice),)
        self.env.synth = DynamicSynth()
        self.start()
        self.assertEqual([setting.id for setting in self.env.synth.supportedSettings], ["dynamic-first", "sonicPitch"])
        self.env.synth.voice = "other"
        self.assertEqual([setting.id for setting in self.env.synth.supportedSettings], ["dynamic-other", "sonicPitch"])
        self.env.get("_setGlobalEnabled")(False)
        self.assertEqual([setting.id for setting in self.env.synth.supportedSettings], ["dynamic-other"])

    def test_synth_wrapper_retains_signature_and_filters_new_keywords(self):
        original = self.env.handler.setSynth
        self.start()
        self.assertEqual(inspect.signature(self.env.handler.setSynth), inspect.signature(original))
        self.assertTrue(self.env.handler.setSynth("otherSynth", unsupportedOption=True))
        self.assertEqual(self.env.synth.name, "otherSynth")
        self.assertEqual(self.env.get("_deferSynthPitchPatchDepth"), 0)

    def test_remote_parameter_order_and_cache_reset(self):
        self.start()
        values = []
        self.env.synth.name = "sapi5_32"
        self.env.synth._remoteService = SimpleNamespace(setParam=lambda name, value: values.append((name, value)))
        apply = self.env.get("_applyRuntimeSonicPitch")
        apply(self.env.synth, 65)
        self.assertEqual(values, [("_sonicPitchExtendedRange", 0), ("_sonicQuality", 0), ("sonicPitch", 65)])
        apply(self.env.synth, 65)
        self.assertEqual(len(values), 3)
        self.env.get("_resetSynthSwitchRuntimeState")()
        apply(self.env.synth, 65)
        self.assertEqual(len(values), 6)

    def test_short_block_callbacks_wait_for_processed_output(self):
        self.start()
        self.env.get("_setCurrentSynthSonicPitch")(65)
        done = []
        player = self.env.WavePlayer()
        with self.env.replace("_getSonicModule", lambda: self.env.sonic):
            player.feed(b"\x01\x00" * 40, onDone=lambda: done.append("first"))
            self.assertEqual(player.blocks, [])
            self.assertEqual(done, [])
            player.feed(b"\x02\x00" * 20, onDone=lambda: done.append("second"))
            self.assertEqual(done, ["first", "second"])
            self.assertEqual(player.blocks, [b"\x01\x00" * 40 + b"\x02\x00" * 20])

    def test_pitch_change_is_deferred_until_next_utterance(self):
        self.start()
        self.env.get("_setCurrentSynthSonicPitch")(65)
        player = self.env.WavePlayer()
        with self.env.replace("_getSonicModule", lambda: self.env.sonic):
            player.feed(b"\x01\x00" * 60)
            initial_pitch = self.env.streams[-1].pitch
            self.env.get("_setCurrentSynthSonicPitch")(35)
            player.feed(b"\x01\x00" * 60)
            self.assertEqual(len(self.env.streams), 1)
            self.assertEqual(self.env.streams[-1].pitch, initial_pitch)
            player.idle()
            player.feed(b"\x01\x00" * 60)
            self.assertEqual(len(self.env.streams), 2)
            self.assertLess(self.env.streams[-1].pitch, 1)

    def test_stop_releases_pending_callbacks_without_flushing_audio(self):
        self.start()
        self.env.get("_setCurrentSynthSonicPitch")(65)
        player = self.env.WavePlayer()
        done = []
        with self.env.replace("_getSonicModule", lambda: self.env.sonic):
            player.feed(b"\x01\x00" * 40, onDone=lambda: done.append("done"))
            player.stop()
            self.assertEqual(done, ["done"])
            self.assertEqual(player.blocks, [])
            self.assertFalse(self.env.get("_playerProcessors"))

    def test_non_speech_and_non_pcm16_bypass_processing(self):
        self.start()
        self.env.get("_setCurrentSynthSonicPitch")(65)
        with self.env.replace("_getSonicModule", lambda: self.env.sonic):
            for player in [self.env.WavePlayer(bits=32), self.env.WavePlayer(purpose=self.env.wave.AudioPurpose.OTHER)]:
                player.feed(b"\x01\x00" * 60)
                self.assertEqual(player.blocks, [b"\x01\x00" * 60])
            self.assertFalse(self.env.streams)

    def test_processing_failure_falls_back_to_original_audio(self):
        self.start()
        self.env.get("_setCurrentSynthSonicPitch")(65)
        player = self.env.WavePlayer()
        with self.env.replace("_getSonicModule", lambda: self.env.sonic):
            player.feed(b"\x01\x00" * 60)
            self.env.streams[-1].fail = True
            player.feed(b"\x02\x00" * 60)
            self.assertEqual(player.blocks[-1], b"\x02\x00" * 60)
            self.assertFalse(self.env.get("_playerProcessors"))

    def test_soundwave_factory_does_not_replace_retained_waveplayer(self):
        plugin = self.start()
        original_class = self.env.WavePlayer
        original_feed = self.env.get("_originalWavePlayerMethods")["feed"]
        factory = lambda *args, **kwargs: original_class(*args, **kwargs)
        self.env.wave.WavePlayer = factory
        self.env.get("_setCurrentSynthSonicPitch")(65)
        with self.env.replace("_getSonicModule", lambda: self.env.sonic):
            player = factory()
            player.feed(b"\x01\x00" * 60)
            player.idle()
            self.assertTrue(player.blocks)
        plugin.terminate()
        self.assertIs(self.env.wave.WavePlayer, factory)
        self.assertIs(original_class.feed, original_feed)

    def test_destroyed_panel_guard_ignores_only_deleted_window_error(self):
        def deleted(panel):
            raise RuntimeError("wrapped C/C++ object has been deleted")
        def unrelated(panel):
            raise RuntimeError("unexpected error")
        panel = SimpleNamespace()
        guard = self.env.get("_makeAutoSettingsRefreshGuiGuard")
        self.assertIsNone(guard(deleted)(panel))
        with self.assertRaisesRegex(RuntimeError, "unexpected error"):
            guard(unrelated)(panel)


if __name__ == "__main__":
    unittest.main()
