import os
import sys
import re
from pathlib import Path

# Pfad zum Android-Projekt (BITTE HIER WEITERHIN MANUELL ANPASSEN)
# project_dir = Path("/Users/admin/AndroidStudioProjects/GDocScanner")
project_dir = Path("c:\\android\\GDocScanner")
# project_dir = Path("c:\\android\\SPTest")

# Ausgabe-Datei (standardmäßig neben dem Script)
output_file = Path("code.txt")

EXCLUDE_DIRS = {".git", ".gradle", ".idea", "build", "captures", ".DS_Store"}
EXCLUDE_FILES = {"Thumbs.db", "desktop.ini"}

SOURCE_EXTS = {".kt", ".java", ".kts"}
XML_ANYWHERE_IN_RES = True
MANIFEST_NAME = "AndroidManifest.xml"

RELEVANT_FILENAMES = {
    "build.gradle", "build.gradle.kts",
    "settings.gradle", "settings.gradle.kts",
    "gradle.properties",
    "gradle-wrapper.properties",
    "libs.versions.toml",
    "proguard-rules.pro", "proguard.pro",
    "google-services.json",
    "local.properties",
}

def is_excluded_dir(path: Path) -> bool:
    parts = {p.name for p in path.parents} | {path.name}
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

# --- Vektor-XMLs erkennen und ausschließen ---------------------------------
VECTOR_ROOT_TAG_RE = re.compile(r"<\s*(?:animated-)?vector\b", re.IGNORECASE)

def _read_text_lenient(p: Path, max_chars: int = 4096) -> str | None:
    encodings = ["utf-8", "utf-16", "latin-1"]
    for enc in encodings:
        try:
            text = p.read_text(encoding=enc, errors="strict")
            return text[:max_chars]
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return None

def is_vector_drawable_xml(p: Path) -> bool:
    head = _read_text_lenient(p, 4096)
    if head is None:
        return False
    return VECTOR_ROOT_TAG_RE.search(head) is not None

# --- NEU: Nur strings.xml aus res/values/ zulassen --------------------------
def is_strings_xml_in_default_values(p: Path) -> bool:
    """
    True nur für .../res/values/strings.xml (ohne Sprach-/Qualifizierer).
    Alles wie .../res/values-de/strings.xml wird ausgeschlossen.
    """
    if p.name.lower() != "strings.xml":
        return False
    parent = p.parent.name.lower()
    return parent == "values"  # bewusst strikt, keine -de, -rDE, -night etc.

def is_named_config(p: Path) -> bool:
    return p.name in RELEVANT_FILENAMES

def is_relevant(p: Path) -> bool:
    if p.is_dir():
        return False
    if p.name in EXCLUDE_FILES:
        return False
    if is_excluded_dir(p.parent):
        return False

    # Schnelle Pfade
    if is_source_file(p) or is_manifest(p) or is_named_config(p):
        return True

    if is_res_xml(p):
        # Falls es eine strings.xml ist: nur aus res/values/ zulassen
        if p.name.lower() == "strings.xml":
            return is_strings_xml_in_default_values(p)

        # Andere XMLs in res/** zulassen – außer Vektorgrafiken
        return not is_vector_drawable_xml(p)

    return False

def to_display_path(p: Path) -> str:
    try:
        return str(p.relative_to(project_dir))
    except Exception:
        return str(p)

def safe_read_text(p: Path) -> str | None:
    encodings = ["utf-8", "utf-16", "latin-1"]
    for enc in encodings:
        try:
            return p.read_text(encoding=enc, errors="strict")
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return None

def enable_windows_long_paths():
    pass

def main():
    if not project_dir.exists():
        print(f"Achtung: Projektpfad nicht gefunden: {project_dir}")
        return

    if os.name == "nt":
        enable_windows_long_paths()

    try:
        if output_file.exists():
            output_file.unlink()
    except OSError as e:
        print(f"Konnte bestehende Ausgabedatei nicht löschen: {output_file} ({e})")

    count = 0
    with output_file.open("w", encoding="utf-8", newline="\n") as out:
        for root, dirs, files in os.walk(project_dir):
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

    sep_hint = "\\" if os.name == "nt" else "/"
    print(f"Fertig. {count} Dateien nach {output_file} geschrieben. (Pfadtrenner: '{sep_hint}')")

    # Größe der erzeugten code.txt in Bytes ausgeben
    try:
        size_bytes = output_file.stat().st_size
        print(f"Dateigröße von {output_file}: {size_bytes} Bytes")
    except OSError as e:
        print(f"Konnte Dateigröße nicht ermitteln: {e}")

if __name__ == "__main__":
    main()

