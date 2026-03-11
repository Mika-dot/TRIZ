from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class StageSpec:
    id: str
    block: str
    title: str
    purpose: str
    required_fields: Dict[str, str]
    quality_checks: List[str]

    def slug(self) -> str:
        safe = self.id.replace('.', '_')
        return f'{safe}_{self.title.lower().replace(" ", "_")}'


@dataclass
class QualityCheck:
    check: str
    status: str
    comment: str


@dataclass
class StageResult:
    stage_id: str
    block: str
    title: str
    summary: str
    deliverables: Dict[str, str]
    quality_checks: List[QualityCheck] = field(default_factory=list)
    handoff: str = ''
    confidence: float = 0.0
    model: str = ''
    raw_content: str = ''

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload['quality_checks'] = [asdict(item) for item in self.quality_checks]
        return payload


@dataclass
class PipelineInput:
    problem: str
    constraints: str = ''
    context_notes: str = ''


@dataclass
class RunArtifacts:
    run_dir: str
    report_path: str
    json_path: str
    summary_path: str
