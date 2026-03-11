from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Tuple

import requests

from triz_agent.config import AppConfig
from triz_agent.models import QualityCheck, StageResult, StageSpec
from triz_agent.prompt_builder import build_repair_prompt


class LMStudioError(RuntimeError):
    pass


class LMStudioClient:
    def __init__(self, config: AppConfig):
        self.config = config

    def _normalize_base_url(self) -> str:
        base = self.config.base_url.rstrip('/')
        if not base.endswith('/v1'):
            base = f'{base}/v1'
        return base

    def list_models(self) -> List[str]:
        url = f'{self._normalize_base_url()}/models'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.config.api_key}'},
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return [item['id'] for item in payload.get('data', []) if 'id' in item]

    def _build_schema(self, stage: StageSpec) -> Dict[str, Any]:
        deliverable_properties = {
            key: {
                'type': 'string',
                'description': description,
            }
            for key, description in stage.required_fields.items()
        }
        return {
            'type': 'json_schema',
            'json_schema': {
                'name': f'triz_stage_{stage.id.replace(".", "_")}',
                'strict': True,
                'schema': {
                    'type': 'object',
                    'properties': {
                        'stage_id': {'type': 'string'},
                        'block': {'type': 'string'},
                        'title': {'type': 'string'},
                        'summary': {'type': 'string'},
                        'deliverables': {
                            'type': 'object',
                            'properties': deliverable_properties,
                            'required': list(stage.required_fields.keys()),
                            'additionalProperties': True,
                        },
                        'quality_checks': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'check': {'type': 'string'},
                                    'status': {'type': 'string'},
                                    'comment': {'type': 'string'},
                                },
                                'required': ['check', 'status', 'comment'],
                                'additionalProperties': False,
                            },
                        },
                        'handoff': {'type': 'string'},
                        'confidence': {'type': 'number'},
                    },
                    'required': [
                        'stage_id',
                        'block',
                        'title',
                        'summary',
                        'deliverables',
                        'quality_checks',
                        'handoff',
                        'confidence',
                    ],
                    'additionalProperties': False,
                },
            },
        }

    def _build_payload(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        stage: StageSpec,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            'stream': False,
            'metadata': {
                'stateless_call_id': str(uuid.uuid4()),
                'stage_id': stage.id,
                'fresh_context': True,
            },
        }
        if self.config.use_structured_output:
            payload['response_format'] = self._build_schema(stage)
        return payload

    @staticmethod
    def _extract_content(response_json: Dict[str, Any]) -> str:
        choices = response_json.get('choices', [])
        if not choices:
            raise LMStudioError('LM Studio вернул пустой список choices.')
        message = choices[0].get('message', {})
        content = message.get('content', '')
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    parts.append(item.get('text', ''))
            return ''.join(parts)
        return json.dumps(content, ensure_ascii=False)

    @staticmethod
    def _validate_stage_json(stage: StageSpec, parsed: Dict[str, Any]) -> None:
        deliverables = parsed.get('deliverables', {})
        missing = [key for key in stage.required_fields if key not in deliverables]
        if missing:
            raise LMStudioError(f'В ответе отсутствуют поля deliverables: {", ".join(missing)}')

    def call_stage(
        self,
        stage: StageSpec,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Tuple[StageResult, Dict[str, Any], str]:
        url = f'{self._normalize_base_url()}/chat/completions'
        last_error = ''
        last_raw_content = ''
        last_payload: Dict[str, Any] = {}
        original_user_prompt = user_prompt

        for attempt in range(self.config.retry_attempts + 1):
            payload = self._build_payload(model=model, system_prompt=system_prompt, user_prompt=user_prompt, stage=stage)
            last_payload = payload
            response = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {self.config.api_key}',
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            if not response.ok:
                response_preview = response.text[:3000]
                raise LMStudioError(
                    f'LM Studio вернул HTTP {response.status_code} на этапе {stage.id} ({stage.title}). '
                    f'Тело ответа: {response_preview}'
                )

            response_json = response.json()
            raw_content = self._extract_content(response_json)
            last_raw_content = raw_content
            try:
                parsed = json.loads(raw_content)
                self._validate_stage_json(stage, parsed)
                result = StageResult(
                    stage_id=parsed.get('stage_id', stage.id),
                    block=parsed.get('block', stage.block),
                    title=parsed.get('title', stage.title),
                    summary=parsed.get('summary', ''),
                    deliverables={key: str(value) for key, value in parsed.get('deliverables', {}).items()},
                    quality_checks=[
                        QualityCheck(
                            check=str(item.get('check', '')),
                            status=str(item.get('status', '')),
                            comment=str(item.get('comment', '')),
                        )
                        for item in parsed.get('quality_checks', [])
                    ],
                    handoff=parsed.get('handoff', ''),
                    confidence=float(parsed.get('confidence', 0.0)),
                    model=model,
                    raw_content=raw_content,
                )
                return result, last_payload, raw_content
            except (json.JSONDecodeError, ValueError, LMStudioError) as exc:
                last_error = str(exc)
                if attempt >= self.config.retry_attempts:
                    break
                repair_json = raw_content[:4000]
                user_prompt = build_repair_prompt(
                    stage=stage,
                    invalid_json=repair_json,
                    error_message=last_error,
                )
                if attempt == 0:
                    user_prompt += '\n\nИсходная постановка текущего этапа (сокращенно):\n' + original_user_prompt[:3000]

        raise LMStudioError(
            'Не удалось получить валидный JSON от LM Studio. '
            f'Этап: {stage.id} ({stage.title}). '
            f'Последняя ошибка: {last_error}. Последний ответ: {last_raw_content[:3000]}'
        )
