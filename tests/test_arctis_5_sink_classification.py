# Copyright (C) 2026 loteran
# SPDX-License-Identifier: GPL-3.0-or-later

"""Arctis 5 (0x12aa): the two stereo PCMs must classify onto separate channels.

The Arctis 5 exposes analog-game and analog-chat, both stereo. The generic
classifier used to tell game from chat by channel count (2ch = game, 1ch =
chat), which leaves chat unmatched and both roles falling onto the same
sink — the first stereo one in the list. With everything routed onto one
PCM the ChatMix dial in the USB box has nothing left to mix.

The classifier now also consults the node.name suffix (analog-game /
analog-chat) before the channel-count fallback, so the two PCMs land where
the routing expects them.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from arctis_sound_manager.pactl import PulseAudioManager


class _Sink:
    def __init__(self, name: str, ch: int):
        self.name = name
        self.channel_count = ch
        self.proplist = {
            "node.name": name,
            "device.vendor.id": "0x1038",
            "device.product.id": "0x12aa",
        }


def _manager(sinks: list[_Sink]) -> PulseAudioManager:
    mgr = PulseAudioManager.__new__(PulseAudioManager)
    mgr.sink_list_wrapper = MagicMock(return_value=sinks)
    return mgr


def _arctis5_sinks() -> list[_Sink]:
    # pulsectl returns sinks in index order; the Arctis 5's chat PCM comes first.
    base = "alsa_output.usb-SteelSeries_SteelSeries_Arctis_5_00000000-00."
    return [_Sink(base + "analog-chat", 2), _Sink(base + "analog-game", 2)]


def test_arctis_5_stereo_pcms_split_game_and_chat():
    mgr = _manager(_arctis5_sinks())

    game, chat = mgr.get_arctis_sinks_classified(
        vendor_id=0x1038, product_id=0x12aa)

    assert game is not None and game.name.endswith("analog-game"), (
        f"game must be the analog-game PCM, got {game and game.name}")
    assert chat is not None and chat.name.endswith("analog-chat"), (
        f"chat must be the analog-chat PCM, got {chat and chat.name}")
    assert game.name != chat.name, "Game and Chat must not collapse onto one PCM"


def test_pro_output_suffix_still_wins_for_other_families():
    """The Nova Pro Wireless' pro-output-1/0 naming keeps its priority.

    The mock sinks keep the Arctis 5 PID from _Sink; the query passes the
    same id so the vendor/product filter lets them through — what this test
    pins is the suffix priority, which is PID-independent.
    """
    base = "alsa_output.usb-SteelSeries_Arctis_Nova_Pro_Wireless-00."
    mgr = _manager([_Sink(base + "pro-output-0", 1), _Sink(base + "pro-output-1", 2)])

    game, chat = mgr.get_arctis_sinks_classified(
        vendor_id=0x1038, product_id=0x12aa)

    assert game.name.endswith("pro-output-1")
    assert chat.name.endswith("pro-output-0")
