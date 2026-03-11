from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from triz_agent.models import QualityCheck, StageResult, StageSpec


class MockLLMClient:
    def __init__(self, *_args: Any, **_kwargs: Any):
        pass

    def list_models(self):
        return ['mock-triz-model-a', 'mock-triz-model-b', 'mock-triz-model-c']

    def call_stage(
        self,
        stage: StageSpec,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Tuple[StageResult, Dict[str, Any], str]:
        base_text = f'Этап {stage.id} ({stage.title}) выполнен в демонстрационном режиме.'
        deliverables = {
            key: f'{description} Демонстрационное содержание для этапа {stage.id}.'
            for key, description in stage.required_fields.items()
        }
        payload = {
            'stage_id': stage.id,
            'block': stage.block,
            'title': stage.title,
            'summary': base_text,
            'deliverables': deliverables,
            'quality_checks': [
                {
                    'check': item,
                    'status': 'ok',
                    'comment': 'Проверка закрыта в демонстрационном режиме.',
                }
                for item in stage.quality_checks
            ],
            'handoff': f'Результаты этапа {stage.id} готовы для следующего шага.',
            'confidence': 0.55,
        }
        result = StageResult(
            stage_id=stage.id,
            block=stage.block,
            title=stage.title,
            summary=base_text,
            deliverables=deliverables,
            quality_checks=[
                QualityCheck(check=item, status='ok', comment='Проверка закрыта в демонстрационном режиме.')
                for item in stage.quality_checks
            ],
            handoff=f'Результаты этапа {stage.id} готовы для следующего шага.',
            confidence=0.55,
            model=model,
            raw_content=json.dumps(payload, ensure_ascii=False),
        )
        request = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'mock_mode': True,
        }
        return result, request, result.raw_content
