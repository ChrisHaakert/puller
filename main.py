import os
from pathlib import Path

# Pfad zum Android-Projekt
project_dir = Path("/Users/admin/AndroidStudioProjects/GDocScanner")
output_file = Path("code.txt")

# Ordner ausschließen (Build-Artefakte, IDE, VCS)
EXCLUDE_DIRS = {".git", ".gradle", ".idea", "build", "captures", ".DS_Store"}

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
}

def is_excluded_dir(path: Path) -> bool:
    parts = set(p.name for p in path.parents) | {path.name}
    return any(name in EXCLUDE_DIRS for name in parts)

def is_source_file(p: Path) -> bool:
    return p.suffix in SOURCE_EXTS

def is_manifest(p: Path) -> bool:
    return p.name == MANIFEST_NAME

def is_res_xml(p: Path) -> bool:
    if not XML_ANYWHERE_IN_RES:
        return False
    parts = [x.lower() for x in p.parts]
    return "res" in parts and p.suffix == ".xml"

def is_named_config(p: Path) -> bool:
    return p.name in RELEVANT_FILENAMES

def is_relevant(p: Path) -> bool:
    # Reihenfolge: schnellste Checks zuerst
    if p.is_dir():
        return False
    if is_excluded_dir(p.parent):
        return False
    return (
        is_source_file(p)
        or is_manifest(p)
        or is_res_xml(p)
        or is_named_config(p)
    )

# Vorherige Datei löschen
if output_file.exists():
    output_file.unlink()

count = 0
with output_file.open("w", encoding="utf-8") as out:
    for root, dirs, files in os.walk(project_dir):
        # Ordner-Filter live anwenden (beschleunigt den Walk)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            p = Path(root) / fn
            if is_relevant(p):
                try:
                    text = p.read_text(encoding="utf-8", errors="strict")
                except UnicodeDecodeError:
                    # Falls doch mal eine Binär-/falsch encodierte Datei reinrutscht, überspringen
                    continue
                out.write(f"\n\n===== Datei: {p} =====\n\n")
                out.write(text)
                count += 1

print(f"Fertig. {count} Dateien nach {output_file} geschrieben.")
