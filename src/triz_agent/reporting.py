from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, List

from triz_agent.models import PipelineInput, RunArtifacts, StageResult


def ensure_run_dir(root: str) -> Path:
    timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
    run_dir = Path(root) / f'run_{timestamp}'
    (run_dir / 'stages').mkdir(parents=True, exist_ok=True)
    return run_dir


def save_stage_log(run_dir: Path, result: StageResult, request_payload: dict, raw_content: str) -> None:
    stage_file = run_dir / 'stages' / f'{result.stage_id.replace(".", "_")}.json'
    stage_file.write_text(
        json.dumps(
            {
                'stage_id': result.stage_id,
                'block': result.block,
                'title': result.title,
                'model': result.model,
                'request': request_payload,
                'response': result.to_dict(),
                'raw_content': raw_content,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )


def build_markdown_report(pipeline_input: PipelineInput, results: Iterable[StageResult]) -> str:
    result_list: List[StageResult] = list(results)
    lines: List[str] = []
    lines.append('# Полный отчёт по ТРИЗ-пайплайну')
    lines.append('')
    lines.append('## Входная задача')
    lines.append('')
    lines.append(pipeline_input.problem.strip())
    lines.append('')
    if pipeline_input.constraints.strip():
        lines.append('## Ограничения')
        lines.append('')
        lines.append(pipeline_input.constraints.strip())
        lines.append('')
    if pipeline_input.context_notes.strip():
        lines.append('## Дополнительный контекст')
        lines.append('')
        lines.append(pipeline_input.context_notes.strip())
        lines.append('')

    current_block = None
    for result in result_list:
        if result.block != current_block:
            current_block = result.block
            lines.append(f'## {current_block}')
            lines.append('')
        lines.append(f'### Этап {result.stage_id}. {result.title}')
        lines.append('')
        lines.append(f'**Модель:** `{result.model}`  ')
        lines.append(f'**Уверенность:** `{result.confidence:.2f}`')
        lines.append('')
        lines.append(result.summary.strip())
        lines.append('')
        lines.append('**Результаты этапа:**')
        lines.append('')
        for key, value in result.deliverables.items():
            lines.append(f'- **{key}**: {value}')
        lines.append('')
        lines.append('**Проверки качества:**')
        lines.append('')
        for item in result.quality_checks:
            lines.append(f'- `{item.status}` {item.check} — {item.comment}')
        lines.append('')
        lines.append(f'**Передача на следующий этап:** {result.handoff}')
        lines.append('')

    if result_list:
        final_result = result_list[-1]
        lines.append('## Итог')
        lines.append('')
        lines.append(final_result.deliverables.get('final_solution', final_result.summary))
        lines.append('')
        lines.append('### Краткий вывод')
        lines.append('')
        lines.append(final_result.deliverables.get('executive_summary', final_result.handoff))
        lines.append('')

    return '\n'.join(lines).strip() + '\n'


def save_run_artifacts(
    run_dir: Path,
    pipeline_input: PipelineInput,
    results: Iterable[StageResult],
) -> RunArtifacts:
    result_list = list(results)
    report_path = run_dir / 'report.md'
    json_path = run_dir / 'results.json'
    summary_path = run_dir / 'summary.txt'

    report_path.write_text(
        build_markdown_report(pipeline_input=pipeline_input, results=result_list),
        encoding='utf-8',
    )
    json_path.write_text(
        json.dumps(
            {
                'input': {
                    'problem': pipeline_input.problem,
                    'constraints': pipeline_input.constraints,
                    'context_notes': pipeline_input.context_notes,
                },
                'results': [result.to_dict() for result in result_list],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    final_summary = result_list[-1].deliverables.get('executive_summary', result_list[-1].summary) if result_list else ''
    summary_path.write_text(final_summary, encoding='utf-8')

    return RunArtifacts(
        run_dir=str(run_dir),
        report_path=str(report_path),
        json_path=str(json_path),
        summary_path=str(summary_path),
    )
