import os

# Pfad zum Android-Projekt
# project_dir = "/Users/admin/AndroidStudioProjects/GrannysRemote"
project_dir = "/Users/admin/AndroidStudioProjects/STest1"

output_file = "code.txt"

# Relevante Dateitypen
source_extensions = {'.kt', '.java'}
gradle_files = {'build.gradle', 'settings.gradle', 'gradle.properties', 'build.gradle.kts'}

# Funktion zum Prüfen, ob es sich um eine Layout-XML-Datei handelt
def is_layout_xml(file_path):
    return "/res/layout/" in file_path.replace("\\", "/") and file_path.endswith(".xml")

# Funktion zum Prüfen, ob es eine relevante Gradle-Datei ist (inkl. .kts)
def is_relevant_gradle_file(file_name):
    return file_name in gradle_files

# Vorherige Datei löschen, falls vorhanden
if os.path.exists(output_file):
    os.remove(output_file)

# Dateien sammeln und schreiben
with open(output_file, 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1]
            if (
                ext in source_extensions or
                is_relevant_gradle_file(file) or
                is_layout_xml(full_path)
            ):
                try:
                    with open(full_path, 'r', encoding='utf-8') as infile:
                        outfile.write(f"\n\n===== Datei: {full_path} =====\n\n")
                        outfile.write(infile.read())
                except Exception as e:
                    print(f"Fehler beim Lesen von {full_path}: {e}")
