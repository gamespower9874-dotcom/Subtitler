# SPDX-License-Identifier: AGPL-3.0-or-later
from app.qc import QCRules, balance_lines, check

def test_balance_lines():
    assert "\n" in balance_lines("one two three four five six", 12)

def test_qc_detects_speed_and_gap():
    segments = [{"start": 0, "end": 1, "text": "This is a very long subtitle line"}, {"start": 1.01, "end": 2, "text": "Next"}]
    issues = check(segments, QCRules(max_cps=5))
    assert any("speed" in message.lower() for _, message in issues)
    assert any("gap" in message.lower() for _, message in issues)
