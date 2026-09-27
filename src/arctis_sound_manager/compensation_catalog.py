# Copyright (C) 2026 loteran
# SPDX-License-Identifier: GPL-3.0-or-later

"""compensation_catalog — bundled headphone compensation (InvHpTF) profiles.

Layer 2 of the spatial stack: an inverse of the headphone's own response, so
the spatial model is judged through flattened drivers instead of on top of
their colourations. The WAVs are AutoEq minimum-phase impulse responses at
48 kHz, one per measured Arctis model; selecting one makes the HeSuVi
generator add two convolvers after the binaural mixdown (see
``sonar_to_pipewire._COMP_DEST``). Only headphone-destined chains get them —
a loudspeaker route is not corrected with a headphone inverse filter.

"none" is not a file: it means the layer is switched off, and the generated
surround chain stays byte-identical to installs that never touched it.
"""
from __future__ import annotations

import csv
import functools
from pathlib import Path

_COMP_DIR = Path(__file__).parent / "compensation_assets"

_NONE_ID = "none"

_NO_COMPENSATION_LABEL = "No headphone compensation"


@functools.lru_cache(maxsize=None)
def _parse_csv() -> dict[str, str]:
    result: dict[str, str] = {}
    csv_path = _COMP_DIR / "info.csv"
    if not csv_path.exists():
        return result
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        for row in reader:
            if len(row) < 2 or row[0].startswith("*"):
                continue
            comp_id = row[0].strip()
            if (_COMP_DIR / f"{comp_id}.wav").exists():
                result[comp_id] = row[1].strip()
    return result


def list_compensation_options() -> list[dict]:
    """Options for the D-Bus list and the settings dropdown.

    "none" comes first: switching the layer off should be the obvious first
    choice, and it is the safe default.
    """
    options = [{"id": _NONE_ID, "name": _NO_COMPENSATION_LABEL}]
    options += [{"id": comp_id, "name": desc} for comp_id, desc in _parse_csv().items()]
    return options


def is_valid_compensation_id(comp_id: str | None) -> bool:
    """True if *comp_id* is "none" or a real entry in the bundled catalogue."""
    if not isinstance(comp_id, str):
        return False
    if comp_id == _NONE_ID:
        return True
    return comp_id in _parse_csv()


def package_compensation_path(comp_id: str) -> Path | None:
    """Absolute path to a bundled compensation WAV, or None.

    "none" has no file on purpose. Only ids present in the catalogue are
    accepted, and the resolved path must stay inside ``_COMP_DIR`` — the same
    two independent guards ``hrir_catalog.package_hrir_path()`` keeps
    (CHA-12), so a hand-edited settings file can never point the convolver at
    an arbitrary file.
    """
    if not is_valid_compensation_id(comp_id) or comp_id == _NONE_ID:
        return None
    path = (_COMP_DIR / f"{comp_id}.wav").resolve()
    if not path.is_relative_to(_COMP_DIR.resolve()) or not path.exists():
        return None
    return path
