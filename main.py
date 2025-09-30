import os
import sys
from pathlib import Path

# Pfad zum Android-Projekt (BITTE HIER WEITERHIN MANUELL ANPASSEN)
project_dir = Path("/Users/admin/AndroidStudioProjects/GDocScanner")
project_dir = Path("c:\\android\\SpTest")

# Ausgabe-Datei (standardmäßig neben dem Script)
output_file = Path("code.txt")

# Ordner ausschließen (Build-Artefakte, IDE, VCS)
EXCLUDE_DIRS = {".git", ".gradle", ".idea", "build", "captures", ".DS_Store"}

# Auf Windows übliche Junk-Dateien ergänzen
EXCLUDE_FILES = {"Thumbs.db", "desktop.ini"}

# Relevante Dateiendungen / -namen
SOURCE_EXTS = {".kt", ".java", ".kts"}  # inkl. Kotlin-Skripte
XML_ANYWHERE_IN_RES = True              # alle XMLs unter .../res/**.xml
MANIFEST_NAME = "AndroidManifest.xml"

# Gradle/Config-Dateien (egal wo sie liegen)
RELEVANT_FILENAMES = {
    "build.gradle", "build.gradle.kts",
    "settings.gradle", "settings.gradle.kts",
    "gradle.properties",
    "gradle-wrapper.properties",
    "libs.versions.toml",              # Version Catalog
    "proguard-rules.pro", "proguard.pro",
    # optional / falls vorhanden:
    "google-services.json",
    # gelegentlich vorhanden:
    "local.properties",
}

def is_excluded_dir(path: Path) -> bool:
    # prüft, ob irgendein Teilpfad ein ausgeschlossener Ordner ist
    parts = {p.name for p in path.parents} | {path.name}
    return any(name in EXCLUDE_DIRS for name in parts)

def is_source_file(p: Path) -> bool:
    return p.suffix in SOURCE_EXTS

def is_manifest(p: Path) -> bool:
    return p.name == MANIFEST_NAME

def is_res_xml(p: Path) -> bool:
    if not XML_ANYWHERE_IN_RES:
        return False
    # case-insensitive Suche nach "res" im Pfad
    parts = [x.lower() for x in p.parts]
    return "res" in parts and p.suffix == ".xml"

def is_named_config(p: Path) -> bool:
    return p.name in RELEVANT_FILENAMES

def is_relevant(p: Path) -> bool:
    # Reihenfolge: schnelle Checks zuerst
    if p.is_dir():
        return False
    if p.name in EXCLUDE_FILES:
        return False
    if is_excluded_dir(p.parent):
        return False
    return (
        is_source_file(p)
        or is_manifest(p)
        or is_res_xml(p)
        or is_named_config(p)
    )

def to_display_path(p: Path) -> str:
    """
    Schreibe relative Pfade zur Lesbarkeit in die Ausgabe.
    Auf Windows werden Backslashes automatisch verwendet.
    """
    try:
        return str(p.relative_to(project_dir))
    except Exception:
        return str(p)

def safe_read_text(p: Path) -> str | None:
    """
    Robust lesen:
    - UTF-8 strikt versuchen
    - Bei Problemen einige gängige Fallbacks probieren
    - Binär-/unlesbare Dateien überspringen (None)
    """
    encodings = ["utf-8", "utf-16", "latin-1"]
    for enc in encodings:
        try:
            return p.read_text(encoding=enc, errors="strict")
        except UnicodeDecodeError:
            continue
        except OSError:
            # z. B. Zugriffsprobleme, zu lange Pfade etc.
            return None
    return None

def enable_windows_long_paths():
    """
    Ab Python 3.8+ sollte Path >260 Zeichen meist ok sein,
    aber falls nötig können wir hier ggf. Hinweise ergänzen.
    (Funktion ist bewusst ein No-Op, damit Script portabel bleibt.)
    """
    pass

def main():
    # Vorbedingungen
    if not project_dir.exists():
        print(f"Achtung: Projektpfad nicht gefunden: {project_dir}")
        return

    # Unter Windows ggf. Long-Path-Handling vorbereiten (No-Op)
    if os.name == "nt":
        enable_windows_long_paths()

    # Vorherige Datei löschen
    try:
        if output_file.exists():
            output_file.unlink()
    except OSError as e:
        print(f"Konnte bestehende Ausgabedatei nicht löschen: {output_file} ({e})")

    count = 0
    with output_file.open("w", encoding="utf-8", newline="\n") as out:
        # os.walk folgt Symlinks standardmäßig nicht -> gut
        for root, dirs, files in os.walk(project_dir):
            # Ordner-Filter live anwenden (beschleunigt den Walk)
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".gradle")]
            for fn in files:
                p = Path(root) / fn
                if is_relevant(p):
                    text = safe_read_text(p)
                    if text is None:
                        continue
                    display = to_display_path(p)
                    out.write(f"\n\n===== Datei: {display} =====\n\n")
                    out.write(text)
                    count += 1

    # Hinweis zu Pfadtrennzeichen je nach OS
    sep_hint = "\\" if os.name == "nt" else "/"
    print(f"Fertig. {count} Dateien nach {output_file} geschrieben. (Pfadtrenner: '{sep_hint}')")

if __name__ == "__main__":
    main()
