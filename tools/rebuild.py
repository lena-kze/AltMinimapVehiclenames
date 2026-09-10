#!/usr/bin/env python3
"""Rebuild der AltMinimapVehiclenamesLena .wotmod (Standalone-Python-Mod).

Ablauf:
  1. Alle .py-Dateien unter modsrc mit Python 2.7 zu .pyc kompilieren
     (py -2 -m py_compile, auf Windows/WSL via cmd.exe).
  2. .wotmod (ZIP_STORED) mit meta.xml + kompilierten Paketdateien packen.
  3. Nach build/ und in das WoT-Mods-Verzeichnis kopieren (falls verfuegbar).

Aufruf:
  python3 tools/rebuild.py            # kompilieren + packen + installieren
  python3 tools/rebuild.py --no-test  # Tests ueberspringen
"""
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
MODSRC = os.path.join(ROOT, "modsrc")
BUILD_DIR = os.path.join(ROOT, "build")
MOD_NAME = "AltMinimapVehiclenames"
WOTMOD = os.path.join(BUILD_DIR, MOD_NAME + ".wotmod")

# WoT-Installationsziel (wird zur Laufzeit geprueft)
MODS_DIRS = [
    "/mnt/j/Wargaming/World_of_Tanks_EU/mods/2.4.0.0",
]
CUSTOM_MODS_DIR = "/mnt/j/Wargaming/World_of_Tanks_EU/Aslain_Modpack/Custom_mods/mods/version"


def py_sources():
    for base, _dirs, names in os.walk(MODSRC):
        for name in names:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def compile_py2_pyc():
    # py2.compilieren: py -2 -m py_compile <...alle Dateien...>
    sources = list(py_sources())
    if not sources:
        raise RuntimeError("Keine .py-Dateien unter modsrc gefunden.")
    rel = [os.path.relpath(p, ROOT).replace("/", "\\") for p in sources]
    cmd = ["cmd.exe", "/c", "py", "-2", "-m", "py_compile"] + rel
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stderr)
        raise RuntimeError("py_compile fehlgeschlagen (rc=%d)" % out.returncode)
    print("Python 2.7 kompiliert: %d Dateien" % len(sources))


def map_entries():
    """(Archivpfad in .wotmod, Quelldatei auf Disk)."""
    entries = [
        ("meta.xml", os.path.join(ROOT, "meta.xml")),
    ]
    pyc_root = os.path.join(MODSRC)
    for p in py_sources():
        rel = os.path.relpath(p, pyc_root)  # z. B. altminimapvehiclenames/.../x.py
        rel = rel[:-3] + ".pyc"
        archive = "res/scripts/client/" + rel[:-4] + ".pyc"
        if rel.endswith("mod_altminimap_vehiclenames.pyc"):
            archive = "res/scripts/client/gui/mods/" + os.path.basename(rel)
        entries.append((archive, p[:-3] + ".pyc"))
    # Uebersetzungen
    trans_dir = os.path.join(MODSRC, "res", "gui", "altminimapvehiclenames", "translations")
    for name in sorted(os.listdir(trans_dir)):
        entries.append(("res/gui/altminimapvehiclenames/translations/" + name,
                        os.path.join(trans_dir, name)))
    return entries


def pack():
    if os.path.exists(WOTMOD):
        os.remove(WOTMOD)
    entries = map_entries()
    with zipfile.ZipFile(WOTMOD, "w", zipfile.ZIP_STORED) as z:
        for archive, src in entries:
            if not os.path.isfile(src):
                raise RuntimeError("Datei fehlt: %s" % src)
            z.write(src, archive)
    print("Paket: %s (%d Bytes)" % (WOTMOD, os.path.getsize(WOTMOD)))


def install():
    for d in MODS_DIRS:
        if os.path.isdir(d):
            dst = os.path.join(d, MOD_NAME + ".wotmod")
            shutil.copy2(WOTMOD, dst)
            print("Installiert: %s" % dst)
    if os.path.isdir(CUSTOM_MODS_DIR):
        dst = os.path.join(CUSTOM_MODS_DIR, MOD_NAME + ".wotmod")
        shutil.copy2(WOTMOD, dst)
        print("Installiert fuer Aslain: %s" % dst)


def run_tests():
    runner = os.path.join(TOOLS, "run_all_tests.py")
    out = subprocess.run([sys.executable, runner], cwd=ROOT)
    if out.returncode != 0:
        raise RuntimeError("Tests fehlgeschlagen (rc=%d) - Build abgebrochen." % out.returncode)
    print("Tests: alle Suiten bestanden")


def main():
    if "--no-test" not in sys.argv:
        run_tests()
    compile_py2_pyc()
    pack()
    install()


if __name__ == "__main__":
    main()
