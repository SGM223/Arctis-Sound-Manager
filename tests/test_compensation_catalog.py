# Copyright (C) 2026 loteran
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for compensation_catalog — bundled headphone compensation (InvHpTF)."""

from arctis_sound_manager import compensation_catalog


def test_none_is_offered_first_and_always_valid():
    options = compensation_catalog.list_compensation_options()
    assert options[0]["id"] == "none"
    assert compensation_catalog.is_valid_compensation_id("none") is True
    # "none" is the layer being off, not a file to convolve with.
    assert compensation_catalog.package_compensation_path("none") is None


def test_bundled_profiles_are_listed_and_resolve():
    ids = {o["id"] for o in compensation_catalog.list_compensation_options()}
    assert "arctis_5_2019" in ids
    assert compensation_catalog.is_valid_compensation_id("arctis_5_2019") is True
    path = compensation_catalog.package_compensation_path("arctis_5_2019")
    assert path is not None and path.suffix == ".wav"


def test_unknown_and_traversing_ids_are_refused():
    assert compensation_catalog.is_valid_compensation_id("not-a-real-id") is False
    assert compensation_catalog.is_valid_compensation_id(None) is False
    # CHA-12: only catalogue members resolve, and the resolved path has to
    # stay inside the asset directory.
    assert compensation_catalog.package_compensation_path("../../../../etc/passwd") is None
    assert compensation_catalog.package_compensation_path("/etc/passwd") is None
