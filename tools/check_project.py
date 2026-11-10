"""Check build inputs and the generated package without importing NVDA modules."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import gettext
import hashlib
from html.parser import HTMLParser
import io
from pathlib import Path, PurePosixPath
import re
import runpy
import string
import sys
import zipfile

import polib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def placeholders(text: str) -> Counter:
    return Counter(field for _, field, _, _ in string.Formatter().parse(text) if field is not None)


class HelpParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.language = None
        self.headings = []
        self.table_headers = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "th":
            self.table_headers += 1
        if tag in ("a", "link"):
            self.links.append(attrs.get("href", ""))


def source_checks(build: dict) -> dict[str, polib.POFile]:
    messages = set()
    for pattern in build["i18nSources"]:
        for path in sorted(ROOT.glob(pattern)):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == "_" and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)):
                    messages.add(node.args[0].value)
    for path in [ROOT / "sconstruct", *ROOT.glob("site_scons/**/*.py"), *ROOT.glob("tools/*.py")]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pot = polib.pofile(str(ROOT / "addon/locale/nvda.pot"))
    require({entry.msgid for entry in pot if not entry.obsolete} == messages,
            "POT differs from source strings; run uv run scons pot")
    catalogs = {}
    for path in sorted(ROOT.glob("addon/locale/*/LC_MESSAGES/nvda.po")):
        lang = path.parents[1].name
        catalog = polib.pofile(str(path))
        require(len(catalog) == len({entry.msgid for entry in catalog}), f"{lang}: duplicate translations")
        require(catalog.metadata.get("Language") == lang, f"{lang}: incorrect Language header")
        require({entry.msgid for entry in catalog if not entry.obsolete} == messages,
                f"{lang}: PO differs from source strings")
        for entry in catalog:
            if entry.obsolete:
                continue
            require(bool(entry.msgstr) and not entry.fuzzy, f"{lang}: untranslated/fuzzy {entry.msgid!r}")
            require(placeholders(entry.msgid) == placeholders(entry.msgstr),
                    f"{lang}: placeholder mismatch: {entry.msgid!r}")
        catalogs[lang] = catalog
    require({"pl", "sk"} <= catalogs.keys(), "Polish or Slovak translation is missing")
    # Local documentation links must resolve in a source checkout. External URLs are not fetched.
    for path in [*ROOT.glob("README*.md"), *ROOT.glob("docs/*.md"), ROOT / "CONTRIBUTING.md", ROOT / "TESTING.md"]:
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" not in link and not link.startswith("#"):
                require((path.parent / link.split("#", 1)[0]).exists(), f"Broken link in {path}: {link}")
    print(f"Sources OK: {len(messages)} messages, {len(catalogs)} complete translations")
    return catalogs


def package_checks(path: Path, build: dict, catalogs: dict) -> None:
    info = build["addon_info"]
    with zipfile.ZipFile(path) as bundle:
        require(bundle.testzip() is None, "Corrupt package")
        names = bundle.namelist()
        require(len(names) == len(set(names)), "Duplicate archive entries")
        expected = {
            "manifest.ini", "installTasks.py", "globalPlugins/globalSonicPitch.py",
            "sapi32HostDrivers/__init__.py", "sapi32HostDrivers/sapi4.py", "sapi32HostDrivers/sapi5.py",
            "globalPlugins/sonicPitchNative/sonic32.dll", "globalPlugins/sonicPitchNative/sonic64.dll",
            "globalPlugins/sonicPitchNative/LICENSE-Sonic.txt", "COPYING.txt",
            "THIRD_PARTY_NOTICES.txt", "doc/style.css",
        }
        for lang in ("en", *catalogs):
            expected.add(f"doc/{lang}/readme.html")
        for lang in catalogs:
            expected.update({f"locale/{lang}/manifest.ini", f"locale/{lang}/LC_MESSAGES/nvda.mo"})
        require(expected <= set(names), f"Missing package files: {expected - set(names)}")
        for name in names:
            item = PurePosixPath(name)
            require(not item.is_absolute() and ".." not in item.parts and "\\" not in name,
                    f"Unsafe archive path: {name}")
            require(not name.startswith("addon/") and "__pycache__" not in item.parts,
                    f"Unexpected package path: {name}")
            require(item.suffix not in {".pyc", ".pyo", ".po", ".pot", ".md"},
                    f"Build input/cache in package: {name}")
            # Source code and native binaries must be packaged byte-for-byte.
            if item.suffix in {".py", ".dll"}:
                require(bundle.read(name) == (ROOT / "addon" / name).read_bytes(), f"Changed bytes: {name}")
        manifest = bundle.read("manifest.ini").decode("utf-8")
        for key, value in {
            "name": info["addon_name"], "version": info["addon_version"],
            "url": info["addon_url"], "docFileName": info["addon_docFileName"],
            "minimumNVDAVersion": info["addon_minimumNVDAVersion"],
            "lastTestedNVDAVersion": info["addon_lastTestedNVDAVersion"],
        }.items():
            require(f"{key} = {value}" in manifest.splitlines(), f"Incorrect manifest field: {key}")
        require(f'description = """{info["addon_description"]}"""' in manifest,
                "Incorrect English manifest description")
        for lang, catalog in catalogs.items():
            compiled = gettext.GNUTranslations(io.BytesIO(bundle.read(f"locale/{lang}/LC_MESSAGES/nvda.mo")))
            for entry in catalog:
                if not entry.obsolete:
                    require(compiled.gettext(entry.msgid) == entry.msgstr, f"{lang}: stale MO")
            description = catalog.find(info["addon_description"]).msgstr
            require(f'description = """{description}"""' in bundle.read(f"locale/{lang}/manifest.ini").decode("utf-8"),
                    f"{lang}: stale translated manifest")
        for lang in ("en", *catalogs):
            parser = HelpParser()
            parser.feed(bundle.read(f"doc/{lang}/readme.html").decode("utf-8"))
            require(parser.language == lang, f"{lang}: incorrect HTML language")
            require(parser.headings.count(1) == 1 and parser.headings[0] == 1,
                    f"{lang}: incorrect main heading")
            require(all(b <= a + 1 for a, b in zip(parser.headings, parser.headings[1:])),
                    f"{lang}: skipped heading level")
            require(parser.table_headers == 3, f"{lang}: missing pitch table headers")
            for link in parser.links:
                if "://" not in link and not link.startswith("#"):
                    from posixpath import normpath
                    target = normpath(f"doc/{lang}/" + link.split("#", 1)[0])
                    require(target in names, f"{lang}: broken help link {link}")
    print(f"Package OK: {path.name} ({len(names)} files)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", nargs="?", const="auto", help="Validate a package; default: current build version")
    parser.add_argument("--write-checksum", action="store_true", help="Write a SHA-256 sidecar for the validated package")
    args = parser.parse_args()
    if args.write_checksum and not args.package:
        parser.error("--write-checksum requires --package")
    build = runpy.run_path(str(ROOT / "buildVars.py"))
    catalogs = source_checks(build)
    if args.package:
        info = build["addon_info"]
        path = ROOT / f'{info["addon_name"]}-{info["addon_version"]}.nvda-addon' if args.package == "auto" else Path(args.package)
        package_checks(path, build, catalogs)
        if args.write_checksum:
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            path.with_suffix(path.suffix + ".sha256").write_text(f"{checksum}  {path.name}\n", encoding="utf-8")
            print(f"SHA-256 written: {checksum}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        sys.exit(f"Validation failed: {error}")
