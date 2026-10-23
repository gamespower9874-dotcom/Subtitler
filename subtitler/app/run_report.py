# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-file pipeline run reports."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_DONE = "done"
STATUS_EMPTY = "empty"
STATUS_SUSPECT = "suspect"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


@dataclass
class FileReport:
    input_path: str
    output_path: str | None = None
    status: str = STATUS_DONE
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None
    segment_count: int = 0
    duration_sec: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str | None = None, **updates: Any) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        if status:
            self.status = status
        for key, value in updates.items():
            setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, output_dir: str | Path, name: str = "run.json") -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / name
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def summarise(reports: list[FileReport]) -> str:
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.status] = counts.get(report.status, 0) + 1
    parts = [f"{status}={count}" for status, count in sorted(counts.items())]
    total_segments = sum(report.segment_count for report in reports)
    return f"{len(reports)} files: " + ", ".join(parts) + f" (segments={total_segments})"
