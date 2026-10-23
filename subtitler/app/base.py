# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common types shared across engines."""
from __future__ import annotations

from typing import TypedDict


class Segment(TypedDict):
    """A single timed transcript segment."""

    start: float
    end: float
    text: str
