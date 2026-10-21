# SPDX-License-Identifier: AGPL-3.0-or-later
from app.translate import translate_segments

class BrokenClient:
    class chat:
        class completions:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("offline")

def test_translation_falls_back_without_network():
    source = [{"start": 0, "end": 1, "text": "Keep me"}]
    assert translate_segments(source, client=BrokenClient())[0]["text"] == "Keep me"
