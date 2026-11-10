"""Add-on settings panel and voluntary support action."""

from __future__ import annotations

from ._nvda import (
	SettingsPanel,
	config,
	guiHelper,
	log,
	ui,
	webbrowser,
	wx,
)
from ._nvda import gettext as _
from . import configuration as _configuration
from . import state as _state


def _openSupportPage() -> None:
	try:
		opened = webbrowser.open_new_tab(_state.SUPPORT_URL)
	except Exception:
		opened = False
		log.debugWarning("globalSonicPitch: failed to open support page", exc_info=True)
	if opened:
		if ui is not None:
			# Translators: Spoken message after opening the support page.
			ui.message(_("Opening support page"))
		return
	if ui is not None:
		# Translators: Spoken error when the support page cannot be opened automatically.
		ui.message(_("Cannot open support page. Open this address manually: {url}").format(url=_state.SUPPORT_URL))


class GlobalSonicPitchSettingsPanel(SettingsPanel):
	# Translators: Title of the add-on settings panel in NVDA preferences.
	title = _("Global Sonic Pitch")

	def makeSettings(self, settingsSizer):
		helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		conf = config.conf[_state.CONFIG_SECTION]
		self.enableCheckbox = helper.addItem(
			# Translators: Checkbox enabling or disabling Sonic pitch processing.
			wx.CheckBox(self, label=_("Enable global Sonic pitch")),
		)
		self.enableCheckbox.SetValue(bool(conf["enabled"]))
		self.extendedRangeCheckbox = helper.addItem(
			# Translators: Checkbox increasing the Sonic pitch control range from 6 to 20 semitones.
			wx.CheckBox(self, label=_("Increase Sonic pitch range to 20 semitones")),
		)
		self.extendedRangeCheckbox.SetValue(bool(conf[_state.EXTENDED_PITCH_RANGE_CONFIG_KEY]))
		self.qualityCheckbox = helper.addItem(
			# Translators: Checkbox enabling Sonic's better-quality processing mode.
			wx.CheckBox(self, label=_("Use better-quality Sonic processing")),
		)
		self.qualityCheckbox.SetValue(_configuration._getSonicQuality() == 1)
		self.qualityDescription = helper.addItem(
			wx.StaticText(
				self,
				# Translators: Help text for Sonic's better-quality processing mode.
				label=_(
					"Better quality may improve Sonic pitch processing for some voices, but can use more CPU. "
					"It does not change the pitch range."
				),
			),
		)
		self.debugCheckbox = helper.addItem(
			# Translators: Checkbox enabling debug log messages for this add-on.
			wx.CheckBox(self, label=_("Enable debug logging")),
		)
		self.debugCheckbox.SetValue(bool(conf["debugLogging"]))
		self.supportButton = helper.addItem(
			# Translators: Button opening the author's support page.
			wx.Button(self, label=_("Support the author")),
		)
		self.enableCheckbox.Bind(wx.EVT_CHECKBOX, self._updateControlState)
		self.supportButton.Bind(wx.EVT_BUTTON, self._onSupport)
		self._updateControlState()

	def _updateControlState(self, event=None):
		enabled = self.enableCheckbox.IsChecked()
		self.extendedRangeCheckbox.Enable(enabled)
		self.qualityCheckbox.Enable(enabled)
		self.qualityDescription.Enable(enabled)
		self.debugCheckbox.Enable(enabled)

	def _onSupport(self, event):
		_openSupportPage()

	def onSave(self):
		_configuration._setConfigValue("debugLogging", self.debugCheckbox.IsChecked())
		_configuration._setSonicQuality(1 if self.qualityCheckbox.IsChecked() else 0)
		_configuration._setExtendedPitchRangeEnabled(self.extendedRangeCheckbox.IsChecked())
		_configuration._setGlobalEnabled(self.enableCheckbox.IsChecked())
		config.conf.save()
