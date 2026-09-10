#!/usr/bin/env python3
"""
Fuehrt alle Mod-Testsuiten aus und meldet eine Gesamtbilanz.

Tests:
  1. test_mod_logic.py      - Battle-Logik (core.py, simulierte Engine-API)
  2. test_settings.py       - Settings-Framework (Params, Config, MSA, Sprache)
  3. test_translations.py   - Parity DE/EN der Uebersetzungsdateien
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, os.pardir))
SUITES = ["test_mod_logic.py", "test_settings.py", "test_translations.py"]


def main():
    failed = []
    for suite in SUITES:
        path = os.path.join(HERE, suite)
        print("=" * 72)
        print("SUITE: %s" % suite)
        print("=" * 72)
        proc = subprocess.run([sys.executable, path], cwd=PROJ)
        if proc.returncode != 0:
            failed.append(suite)
    print("=" * 72)
    if failed:
        print("GESAMT: FEHLGESCHLAGEN - %s" % ", ".join(failed))
        sys.exit(1)
    print("GESAMT: Alle Test-Suiten bestanden.")
    sys.exit(0)


if __name__ == "__main__":
    main()