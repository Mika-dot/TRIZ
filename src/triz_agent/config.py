from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AppConfig:
    base_url: str = 'http://172.31.0.153:49572/v1'
    api_key: str = 'lm-studio'
    default_model: str = 'REPLACE_WITH_LOADED_MODEL'
    fallback_models: List[str] = field(default_factory=list)
    stage_model_map: Dict[str, str] = field(default_factory=dict)
    model_selection_strategy: str = 'round_robin'
    pipeline_profile: str = 'slm_full'
    use_structured_output: bool = True
    temperature: float = 0.2
    max_tokens: int = 1400
    timeout_seconds: int = 180
    retry_attempts: int = 2
    max_context_chars: int = 22000
    project_language: str = 'ru'
    output_root: str = 'runs'
    runtime_guard_enabled: bool = False
    runtime_guard_max_gpu_temp_c: Optional[float] = None
    runtime_guard_max_vram_pct: Optional[float] = None

    @classmethod
    def from_file(cls, path: str | Path) -> 'AppConfig':
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(**raw)

    def to_dict(self) -> Dict[str, object]:
        return {
            'base_url': self.base_url,
            'api_key': self.api_key,
            'default_model': self.default_model,
            'fallback_models': self.fallback_models,
            'stage_model_map': self.stage_model_map,
            'model_selection_strategy': self.model_selection_strategy,
            'pipeline_profile': self.pipeline_profile,
            'use_structured_output': self.use_structured_output,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout_seconds': self.timeout_seconds,
            'retry_attempts': self.retry_attempts,
            'max_context_chars': self.max_context_chars,
            'project_language': self.project_language,
            'output_root': self.output_root,
            'runtime_guard_enabled': self.runtime_guard_enabled,
            'runtime_guard_max_gpu_temp_c': self.runtime_guard_max_gpu_temp_c,
            'runtime_guard_max_vram_pct': self.runtime_guard_max_vram_pct,
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def pick_model(self, stage_id: str, stage_index: int) -> str:
        if stage_id in self.stage_model_map:
            return self.stage_model_map[stage_id]
        if self.fallback_models:
            if self.model_selection_strategy == 'round_robin':
                return self.fallback_models[stage_index % len(self.fallback_models)]
            return self.fallback_models[0]
        return self.default_model
