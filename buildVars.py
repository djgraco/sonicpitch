# Build configuration for Global Sonic Pitch.
# Based on NV Access's NVDA Add-on Template; see docs/building.md.
from site_scons.site_tools.NVDATool.typings import AddonInfo
from site_scons.site_tools.NVDATool.utils import _

addon_info = AddonInfo(
	addon_name="globalSonicPitch",
	# Translators: Add-on name. Keep the product name unchanged.
	addon_summary=_("Global Sonic Pitch"),
	# Translators: Description shown when installing the add-on and in the Add-on Store.
	addon_description=_(
		"Lets you lower or raise the pitch of NVDA speech using Sonic, independently of the "
		"synthesizer's own pitch setting. Remembers separate settings for individual voices."
	),
	# Repository maintenance only: do not claim a new release or NVDA 2027.1 compatibility.
	addon_version="1.1.8",
	addon_changelog="",
	addon_author="Kazimierz Parzych, DJ Graco",
	addon_url="https://github.com/djgraco/sonicpitch",
	addon_sourceURL="https://github.com/djgraco/sonicpitch",
	addon_docFileName="readme.html",
	addon_minimumNVDAVersion="2025.1.0",
	addon_lastTestedNVDAVersion="2026.1.1",
	addon_updateChannel=None,
	addon_license="GPL-2.0-or-later",
	addon_licenseURL="https://github.com/djgraco/sonicpitch/blob/main/COPYING.txt",
)

pythonSources = ["addon/**/*.py"]
i18nSources = pythonSources + ["buildVars.py"]
excludedFiles = [
	"__pycache__/*", "*.pyc", "*.pyo", "*.po", "*.pot", "*.md",
]
baseLanguage = "en"
markdownExtensions = ["markdown.extensions.tables", "markdown.extensions.sane_lists"]
brailleTables = {}
symbolDictionaries = {}
speechDictionaries = {}
