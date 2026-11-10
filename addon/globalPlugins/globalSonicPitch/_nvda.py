"""Shared imports and optional NVDA integration, initialized once."""

from __future__ import annotations

import ctypes
import functools
import inspect
import json
import os
import threading
import time
import webbrowser
import weakref
from typing import Any, Callable

import addonHandler
import config
import globalPluginHandler
import gui
import nvwave
import wx
import gui.settingsDialogs as settingsDialogs
try:
	import globalVars
except Exception:
	globalVars = None
from gui import guiHelper
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from logHandler import log
from scriptHandler import script

try:
	from autoSettingsUtils.driverSetting import NumericDriverSetting
except Exception:
	NumericDriverSetting = None

try:
	import synthDriverHandler
	import ui
except Exception:
	synthDriverHandler = None
	ui = None

try:
	addonHandler.initTranslation()
except Exception:
	pass

try:
	_
except NameError:
	_ = lambda message: message

gettext = _
