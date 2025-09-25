#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import argparse

# ----------------------------------------
# Plattform erkennen & Standardpfade setzen
# ----------------------------------------
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

def default_project_dir() -> Path:
    if IS_WINDOWS:
        # Beispiel-Standardpfad unter Windows
        return Path(r"C:\Android\GDocScanner")
    elif IS_MAC:
        # Beispiel-Standardpfad unter macOS
        return Path.home() / "AndroidStudioProjects" / "MyAndroidProject"
    else:
        # Fallback für Linux/andere
        return Path.cwd()

# ----------------------------------------
# Relevanz-Prüfungen
# ----------------------------------------
SOURCE_EXTENSIONS = {".kt", ".java"}
GRADLE_FILES = {
    "build.gradle",
    "settings.gradle",
    "gradle.properties",
    "build.gradle.kts",
    # häufige zusätzliche Gradle-Dateien
    "settings.gradle.kts",
    "gradle-wrapper.properties",
}
# Ordner, die typischerweise übersprungen werden sollten
SKIP_DIRS = {".git", ".gradle", "build", "out", ".idea"}

def is_layout_xml(path: Path) -> bool:
    """
    Prüft, ob es sich um eine Layout-XML handelt: */src/*/res/layout/*.xml
    """
    # Wir prüfen die Pfadteile robust mit Path.parts
    parts = [p.lower() for p in path.parts]
    if "res" in parts and "layout" in parts and path.suffix.lower() == ".xml":
      # einfache Heuristik: es muss .../res/layout/... enthalten sein
      # (nicht nur irgendein 'layout' im Namen)
      try:
          res_idx = parts.index("res")
          # danach irgendwo 'layout'
          return "layout" in parts[res_idx + 1 :]
      except ValueError:
          return False
    return False

def is_relevant_gradle_file(name: str) -> bool:
    return name in GRADLE_FILES

def should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS or dirname.startswith(".")

# ----------------------------------------
# Dateien sammeln & schreiben
# ----------------------------------------
def collect_and_write(project_dir: Path, output_file: Path) -> None:
    if not project_dir.exists():
        print(f"Warnung: Projektpfad existiert nicht: {project_dir}", file=sys.stderr)

    # Vorherige Datei löschen, falls vorhanden
    if output_file.exists():
        try:
            output_file.unlink()
        except Exception as e:
            print(f"Konnte bestehende Ausgabedatei nicht löschen: {e}", file=sys.stderr)

    with output_file.open("w", encoding="utf-8", errors="replace") as outfile:
        for root, dirs, files in os.walk(project_dir):
            # Verzeichnisse filtern (in-place, damit os.walk sie nicht betritt)
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]

            root_path = Path(root)
            for fname in files:
                fpath = root_path / fname
                ext = fpath.suffix.lower()

                if (
                    ext in SOURCE_EXTENSIONS
                    or is_relevant_gradle_file(fname)
                    or is_layout_xml(fpath)
                ):
                    try:
                        # robustes Lesen; falls UTF-8 nicht reicht, Zeichen ersetzen
                        with fpath.open("r", encoding="utf-8", errors="replace") as infile:
                            rel = fpath.as_posix()
                            outfile.write(f"\n\n===== Datei: {rel} =====\n\n")
                            outfile.write(infile.read())
                    except Exception as e:
                        print(f"Fehler beim Lesen von {fpath}: {e}", file=sys.stderr)

# ----------------------------------------
# CLI
# ----------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Sammelt relevante Android-Projektdateien (Kotlin/Java/Gradle/Layout-XML) in eine Textdatei."
    )
    parser.add_argument(
        "-p", "--project",
        type=Path,
        default=default_project_dir(),
        help="Pfad zum Android-Projekt (Standard abhängig von der Plattform)."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("code.txt"),
        help="Ausgabedatei (Standard: code.txt)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    collect_and_write(args.project.resolve(), args.output.resolve())
    print(f"Fertig. Ausgabe: {args.output.resolve()}")

if __name__ == "__main__":
    main()
