"""NVDA entry point, lifecycle and existing input gesture identities."""

from __future__ import annotations

from ._nvda import (
	NVDASettingsDialog,
	config,
	globalPluginHandler,
	script,
	ui,
)
from ._nvda import gettext as _
from . import audio as _audio
from . import configuration as _configuration
from . import dialogs as _dialogs
from . import host as _host
from . import settings_panel as _settings_panel
from . import state as _state
from . import synths as _synths


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: Input Gestures category for this add-on.
	scriptCategory = _("Global Sonic Pitch")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		_configuration._ensureConfigSpec()
		_host._installSapi32HostDriverPatch()
		_audio.installWavePlayerHook()
		_synths.installSynthPitchHook()
		_dialogs.installVoiceSettingsDialogHook()
		if _settings_panel.GlobalSonicPitchSettingsPanel not in NVDASettingsDialog.categoryClasses:
			NVDASettingsDialog.categoryClasses.append(_settings_panel.GlobalSonicPitchSettingsPanel)

	def terminate(self):
		try:
			if _settings_panel.GlobalSonicPitchSettingsPanel in NVDASettingsDialog.categoryClasses:
				NVDASettingsDialog.categoryClasses.remove(_settings_panel.GlobalSonicPitchSettingsPanel)
		finally:
			_dialogs.uninstallVoiceSettingsDialogHook()
			_synths.uninstallSynthPitchHook()
			_audio.uninstallWavePlayerHook()
			_host._restoreSapi32HostDriverPatch()
			super().terminate()

	@script(
		# Translators: Input gesture description for toggling the add-on.
		description=_("Toggle global Sonic pitch"),
		category=scriptCategory,
	)
	def script_toggleGlobalSonicPitch(self, gesture):
		enabled = not bool(_configuration._getConfigValue("enabled", False))
		_configuration._setGlobalEnabled(enabled)
		config.conf.save()
		if ui is not None:
			# Translators: Spoken status when global Sonic pitch has been enabled or disabled.
			ui.message(_("Global Sonic pitch on") if enabled else _("Global Sonic pitch off"))

	@script(
		# Translators: Input gesture description for reporting the add-on status.
		description=_("Report global Sonic pitch status"),
		category=scriptCategory,
	)
	def script_reportGlobalSonicPitch(self, gesture):
		enabled = bool(_configuration._getConfigValue("enabled", False))
		synth = _synths._getCurrentSynth()
		synthName = _synths._getSynthName(synth)
		if enabled and _synths._isGlobalAudioSupportedSynth(synthName):
			pitch = _configuration._getSonicPitchForSynth(synth)
			# Translators: Spoken status. {synth} is a synthesizer name, {pitch} is a number from 0 to 100.
			message = _("Global Sonic pitch on, {synth} Sonic pitch {pitch}").format(
				synth=synthName or _synths._getCurrentSynthDisplayName(),
				pitch=pitch,
			)
		elif enabled:
			# Translators: Spoken status when the current synth cannot be processed by Sonic. {synth} is a synth name.
			message = _("Global Sonic pitch on, Sonic pitch is unavailable for {synth}").format(
				synth=synthName or _synths._getCurrentSynthDisplayName(),
			)
		else:
			# Translators: Spoken status when global Sonic pitch is disabled.
			message = _("Global Sonic pitch off")
		if _state._sonicUnavailableReason:
			# Translators: Diagnostic status suffix. {reason} is a technical error description.
			message = f"{message}. " + _("Sonic unavailable: {reason}").format(reason=_state._sonicUnavailableReason)
		if ui is not None:
			ui.message(message)

	@script(
		# Translators: Input gesture description for opening the author's support page.
		description=_("Open support page"),
		category=scriptCategory,
	)
	def script_openSupportPage(self, gesture):
		_settings_panel._openSupportPage()

	@script(
		# Translators: Input gesture description for increasing Sonic pitch for the current synth.
		description=_("Increase Sonic pitch for the current synthesizer"),
		category=scriptCategory,
	)
	def script_increaseGlobalSonicPitch(self, gesture):
		pitch = _configuration._changeCurrentSynthSonicPitch(5)
		config.conf.save()
		if ui is not None:
			if pitch is None:
				# Translators: Spoken message when Sonic pitch is unavailable. {synth} is a synth name.
				ui.message(_("Sonic pitch is unavailable for {synth}").format(synth=_synths._getCurrentSynthDisplayName()))
			else:
				# Translators: Spoken message after changing Sonic pitch. {pitch} is a number from 0 to 100.
				ui.message(_("Sonic pitch {pitch}").format(pitch=pitch))

	@script(
		# Translators: Input gesture description for decreasing Sonic pitch for the current synth.
		description=_("Decrease Sonic pitch for the current synthesizer"),
		category=scriptCategory,
	)
	def script_decreaseGlobalSonicPitch(self, gesture):
		pitch = _configuration._changeCurrentSynthSonicPitch(-5)
		config.conf.save()
		if ui is not None:
			if pitch is None:
				# Translators: Spoken message when Sonic pitch is unavailable. {synth} is a synth name.
				ui.message(_("Sonic pitch is unavailable for {synth}").format(synth=_synths._getCurrentSynthDisplayName()))
			else:
				# Translators: Spoken message after changing Sonic pitch. {pitch} is a number from 0 to 100.
				ui.message(_("Sonic pitch {pitch}").format(pitch=pitch))

	@script(
		# Translators: Input gesture description for resetting Sonic pitch for the current synth.
		description=_("Reset Sonic pitch for the current synthesizer"),
		category=scriptCategory,
	)
	def script_resetGlobalSonicPitch(self, gesture):
		pitch = _configuration._setCurrentSynthSonicPitch(_state.NEUTRAL_PITCH)
		config.conf.save()
		if ui is not None:
			if pitch is None:
				# Translators: Spoken message when Sonic pitch is unavailable. {synth} is a synth name.
				ui.message(_("Sonic pitch is unavailable for {synth}").format(synth=_synths._getCurrentSynthDisplayName()))
			else:
				# Translators: Spoken message after changing Sonic pitch. {pitch} is a number from 0 to 100.
				ui.message(_("Sonic pitch {pitch}").format(pitch=pitch))
