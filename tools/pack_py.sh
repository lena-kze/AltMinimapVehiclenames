#!/usr/bin/env bash
set -euo pipefail

# World of Tanks Mod Packing Script (macOS) - Standalone PYTHON Mod
# Erzeugt aus modsrc/mod_altminimap_vehiclenames.pyc + meta.xml die .wotmod.
#
# Voraussetzung (einmalig, auf Windows mit Python 2.7):
#   C:\Python27\python.exe -m py_compile modsrc\mod_altminimap_vehiclenames.py
#   -> erzeugt modsrc\mod_altminimap_vehiclenames.pyc
#
# Danach hier ausfuehren:
#   ./tools/pack_py.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

MOD_NAME="AltMinimapVehiclenames"
PYC_SRC="$ROOT_DIR/modsrc/mod_altminimap_vehiclenames.pyc"
META_XML="$ROOT_DIR/meta.xml"
BUILD_DIR="$ROOT_DIR/build"
TMP_DIR="$ROOT_DIR/build_py_tmp"

if [ ! -f "$PYC_SRC" ]; then
  echo "[Fehler] $PYC_SRC nicht gefunden." >&2
  echo "Bitte zuerst auf Windows mit Python 2.7 kompilieren:" >&2
  echo "  C:\\Python27\\python.exe -m py_compile modsrc\\mod_altminimap_vehiclenames.py" >&2
  exit 1
fi

step() { echo ""; echo "== $1 =="; }

step "1 - Bereinige und lege Arbeitsordner an"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR/res/scripts/client/gui/mods" "$BUILD_DIR"

step "2 - Kopiere kompilierte .pyc"
cp "$PYC_SRC" "$TMP_DIR/res/scripts/client/gui/mods/mod_altminimap_vehiclenames.pyc"

step "3 - Kopiere meta.xml"
cp "$META_XML" "$TMP_DIR/meta.xml"

step "4 - Packe .wotmod (ZIP ohne Kompression)"
( cd "$TMP_DIR" && zip -0 -r -X "$BUILD_DIR/$MOD_NAME.wotmod" meta.xml res/ )

step "5 - Aufräumen"
rm -rf "$TMP_DIR"

echo ""
echo "=============================="
echo "Fertig: $BUILD_DIR/$MOD_NAME.wotmod"
echo "=============================="
