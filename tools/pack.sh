#!/usr/bin/env bash
set -euo pipefail

# World of Tanks Mod Packing Script (macOS)
# Erzeugt aus der per FFDec-GUI gepatchten battle.swf die .wotmod.
#
# Ablauf:
#   1. In FFDec (GUI) die Datei patch_work/battle.swf öffnen
#   2. Die AS3-Klassen editieren (siehe docs/GUI-ANLEITUNG.md)
#   3. In FFDec speichern (Cmd+S) -> patch_work/battle.swf wird überschrieben
#   4. Dieses Skript ausführen -> build/AltMinimapVehiclenames.wotmod

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

MOD_NAME="AltMinimapVehiclenames"
PATCHED_SWF="$ROOT_DIR/patch_work/battle.swf"
META_XML="$ROOT_DIR/meta.xml"
BUILD_DIR="$ROOT_DIR/build"
TMP_DIR="$ROOT_DIR/build_tmp"

if [ ! -f "$PATCHED_SWF" ]; then
  echo "[Fehler] $PATCHED_SWF nicht gefunden." >&2
  echo "Bitte vorher orig/battle.swf nach patch_work/battle.swf kopieren und dort in FFDec patchen." >&2
  exit 1
fi

step() { echo ""; echo "== $1 =="; }

step "1 - Bereinige und lege Arbeitsordner an"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR/res/gui/flash" "$BUILD_DIR"

step "2 - Kopiere gepatchte battle.swf"
cp "$PATCHED_SWF" "$TMP_DIR/res/gui/flash/battle.swf"

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
