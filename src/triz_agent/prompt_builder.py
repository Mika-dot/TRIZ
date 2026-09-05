from __future__ import annotations

import json
from typing import Dict, Iterable, List

from triz_agent.models import PipelineInput, StageResult, StageSpec


SYSTEM_PROMPT = '''Ты инженер-аналитик по ТРИЗ, ФСА, АРИЗ и архитектурам малых языковых моделей.
Работай строго в рамках текущего этапа.
Не выдумывай факты, измерения, номера стандартов, характеристики оборудования или источники, которых нет во входе.
Явно различай: входные данные, логический вывод, гипотезу, неизвестное и требующее внешней проверки утверждение.
Для LLM/RAG не считай уверенность самой модели доказательством истинности. При недостатке evidence предлагай проверку, retrieval, инструмент или отказ от утверждения.
Численные метрики и аппаратные лимиты без фактических измерений/документации обозначай как неизвестные или оценочные.
Отвечай только валидным JSON без markdown и без пояснений вне JSON.
Твоя задача — дать содержательный, но компактный результат, пригодный для передачи в следующий этап пайплайна.
'''


def build_context(results: Iterable[StageResult], max_chars: int) -> str:
    chunks: List[str] = []
    for result in results:
        chunks.append(
            f'[{result.stage_id}] {result.title}\n'
            f'Сводка: {result.summary}\n'
            f'Поля: {json.dumps(result.deliverables, ensure_ascii=False)}\n'
            f'Передача дальше: {result.handoff}\n'
        )
    joined = '\n'.join(chunks)
    if len(joined) <= max_chars:
        return joined
    return joined[-max_chars:]


def build_user_prompt(
    stage: StageSpec,
    pipeline_input: PipelineInput,
    prior_results: List[StageResult],
    max_context_chars: int,
) -> str:
    required_lines = '\n'.join(
        f'- {key}: {description}' for key, description in stage.required_fields.items()
    )
    quality_lines = '\n'.join(f'- {item}' for item in stage.quality_checks)
    prior_context = build_context(prior_results, max_chars=max_context_chars)

    payload: Dict[str, str] = {
        'этап_id': stage.id,
        'блок': stage.block,
        'этап': stage.title,
        'цель_этапа': stage.purpose,
        'исходная_задача': pipeline_input.problem.strip(),
        'ограничения': pipeline_input.constraints.strip() or 'Не указаны отдельно.',
        'дополнительные_заметки': pipeline_input.context_notes.strip() or 'Нет.',
        'контекст_предыдущих_этапов': prior_context or 'Предыдущих этапов нет.',
        'обязательные_поля': required_lines,
        'проверки_качества': quality_lines,
        'эпистемическая_дисциплина': (
            'Не заполняй пробелы правдоподобными выдумками. Для каждого спорного факта укажи, '
            'является ли он входным данным, выводом, гипотезой или требует внешней проверки.'
        ),
        'формат_ответа': (
            'Верни JSON со структурой: '
            '{"stage_id": str, "block": str, "title": str, "summary": str, '
            '"deliverables": object, "quality_checks": array, "handoff": str, "confidence": number}. '
            'В deliverables обязательно заполни все поля текущего этапа.'
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_repair_prompt(stage: StageSpec, invalid_json: str, error_message: str) -> str:
    required_lines = ', '.join(stage.required_fields.keys())
    payload = {
        'задача': 'Исправить предыдущий ответ и вернуть только валидный JSON.',
        'этап_id': stage.id,
        'этап': stage.title,
        'обязательные_поля': required_lines,
        'ошибка': error_message,
        'предыдущий_ответ': invalid_json,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
