from __future__ import annotations

import argparse
import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for

from triz_agent.config import AppConfig
from triz_agent.llm_client import LMStudioClient, LMStudioError
from triz_agent.mock_client import MockLLMClient
from triz_agent.models import PipelineInput, StageResult
from triz_agent.orchestrator import TrizOrchestrator
from triz_agent.stage_catalog import STAGES


@dataclass
class JobState:
    id: str
    created_at: str
    status: str = 'queued'
    problem: str = ''
    constraints: str = ''
    context_notes: str = ''
    mock: bool = False
    stage_index: int = 0
    total_stages: int = 0
    current_stage_id: str = ''
    current_stage_title: str = ''
    run_dir: str = ''
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str = ''
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'created_at': self.created_at,
            'status': self.status,
            'problem': self.problem,
            'constraints': self.constraints,
            'context_notes': self.context_notes,
            'mock': self.mock,
            'stage_index': self.stage_index,
            'total_stages': self.total_stages,
            'progress_percent': int((self.stage_index / self.total_stages) * 100) if self.total_stages else 0,
            'current_stage_id': self.current_stage_id,
            'current_stage_title': self.current_stage_title,
            'run_dir': self.run_dir,
            'run_id': Path(self.run_dir).name if self.run_dir else '',
            'results': self.results,
            'error': self.error,
            'artifacts': self.artifacts,
        }


class JobRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobState] = {}

    def add(self, job: JobState) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields: Any) -> JobState | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            for key, value in fields.items():
                setattr(job, key, value)
            return job

    def append_result(self, job_id: str, result: dict[str, Any]) -> JobState | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.results.append(result)
            return job

    def list(self) -> list[JobState]:
        with self._lock:
            return list(self._jobs.values())


def create_app(project_root: str | Path | None = None, config_path: str | Path | None = None, runs_root: str | Path | None = None) -> Flask:
    root = Path(project_root or Path(__file__).resolve().parents[2]).resolve()
    default_config = root / 'config' / 'default_config.json'
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
    )
    app.config['PROJECT_ROOT'] = str(root)
    app.config['CONFIG_PATH'] = str(Path(config_path).resolve() if config_path else default_config)
    app.config['RUNS_ROOT'] = str((root / (runs_root or 'runs')).resolve()) if not Path(str(runs_root or 'runs')).is_absolute() else str(Path(str(runs_root)).resolve())
    app.config['JOBS'] = JobRegistry()
    app.config['EXAMPLE_PROBLEM'] = read_text_if_exists(root / 'examples' / 'problem_ru.txt')
    app.config['EXAMPLE_CONSTRAINTS'] = read_text_if_exists(root / 'examples' / 'constraints_ru.txt')

    @app.template_filter('nl2br')
    def nl2br(value: Any) -> str:
        text = str(value or '')
        return text.replace('\n', '<br>')

    @app.template_filter('confidence_badge')
    def confidence_badge(value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 'muted'
        if number >= 0.85:
            return 'good'
        if number >= 0.65:
            return 'warn'
        return 'bad'

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {
            'app_title': 'TRIZ Agent Studio',
            'runs_root': app.config['RUNS_ROOT'],
        }

    @app.get('/')
    def index():
        recent_runs = discover_runs(Path(app.config['RUNS_ROOT']), limit=12)
        active_jobs = [job.to_dict() for job in app.config['JOBS'].list() if job.status in {'queued', 'running'}]
        return render_template(
            'index.html',
            recent_runs=recent_runs,
            active_jobs=active_jobs,
            example_problem=app.config['EXAMPLE_PROBLEM'],
            example_constraints=app.config['EXAMPLE_CONSTRAINTS'],
            form_data={
                'problem': app.config['EXAMPLE_PROBLEM'],
                'constraints': app.config['EXAMPLE_CONSTRAINTS'],
                'context_notes': '',
            },
        )

    @app.post('/solve')
    def solve():
        problem = (request.form.get('problem') or '').strip()
        constraints = (request.form.get('constraints') or '').strip()
        context_notes = (request.form.get('context_notes') or '').strip()
        mock = request.form.get('mock') == 'on'

        if not problem:
            recent_runs = discover_runs(Path(app.config['RUNS_ROOT']), limit=12)
            return render_template(
                'index.html',
                recent_runs=recent_runs,
                active_jobs=[job.to_dict() for job in app.config['JOBS'].list() if job.status in {'queued', 'running'}],
                example_problem=app.config['EXAMPLE_PROBLEM'],
                example_constraints=app.config['EXAMPLE_CONSTRAINTS'],
                form_data={
                    'problem': problem,
                    'constraints': constraints,
                    'context_notes': context_notes,
                },
                form_error='Введите описание проблемы.',
            ), 400

        job_id = uuid.uuid4().hex[:12]
        job = JobState(
            id=job_id,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status='queued',
            problem=problem,
            constraints=constraints,
            context_notes=context_notes,
            mock=mock,
            total_stages=len(STAGES),
        )
        app.config['JOBS'].add(job)
        thread = threading.Thread(target=_run_job, args=(app, job_id), daemon=True)
        thread.start()
        return redirect(url_for('job_detail', job_id=job_id))

    @app.get('/jobs/<job_id>')
    def job_detail(job_id: str):
        job = app.config['JOBS'].get(job_id)
        if not job:
            abort(404)
        return render_template('job.html', job=job.to_dict())

    @app.get('/api/jobs/<job_id>')
    def api_job(job_id: str):
        job = app.config['JOBS'].get(job_id)
        if not job:
            return jsonify({'error': 'job_not_found'}), 404
        return jsonify(job.to_dict())

    @app.get('/runs/<run_id>')
    def run_detail(run_id: str):
        run_dir = safe_run_dir(Path(app.config['RUNS_ROOT']), run_id)
        run_data = load_run_data(run_dir)
        if not run_data:
            abort(404)
        return render_template('run_detail.html', run=run_data)

    @app.get('/download/<run_id>/<artifact_name>')
    def download_artifact(run_id: str, artifact_name: str):
        allowed = {'report.md', 'results.json', 'summary.txt'}
        if artifact_name not in allowed:
            abort(404)
        run_dir = safe_run_dir(Path(app.config['RUNS_ROOT']), run_id)
        artifact_path = run_dir / artifact_name
        if not artifact_path.exists():
            abort(404)
        return send_file(artifact_path, as_attachment=True, download_name=artifact_name)

    @app.get('/health')
    def health():
        config_ok = Path(app.config['CONFIG_PATH']).exists()
        runs_ok = Path(app.config['RUNS_ROOT']).exists()
        return jsonify({
            'status': 'ok',
            'config_path': app.config['CONFIG_PATH'],
            'runs_root': app.config['RUNS_ROOT'],
            'config_exists': config_ok,
            'runs_exists': runs_ok,
        })

    return app


def _run_job(app: Flask, job_id: str) -> None:
    registry: JobRegistry = app.config['JOBS']
    job = registry.get(job_id)
    if not job:
        return

    try:
        registry.update(job_id, status='running')
        config = AppConfig.from_file(app.config['CONFIG_PATH'])
        client = MockLLMClient() if job.mock else LMStudioClient(config)
        orchestrator = TrizOrchestrator(config=config, client=client)
        pipeline_input = PipelineInput(
            problem=job.problem,
            constraints=job.constraints,
            context_notes=job.context_notes,
        )

        def on_progress(stage_index: int, total_stages: int, stage, result: StageResult, run_dir: str) -> None:
            registry.update(
                job_id,
                stage_index=stage_index,
                total_stages=total_stages,
                current_stage_id=result.stage_id,
                current_stage_title=result.title,
                run_dir=run_dir,
            )
            registry.append_result(job_id, compact_stage_payload(result))

        output = orchestrator.run(
            pipeline_input=pipeline_input,
            output_root=app.config['RUNS_ROOT'],
            progress_callback=on_progress,
        )
        run_id = Path(output.artifacts.run_dir).name
        registry.update(
            job_id,
            status='completed',
            run_dir=output.artifacts.run_dir,
            artifacts={
                'report_path': output.artifacts.report_path,
                'json_path': output.artifacts.json_path,
                'summary_path': output.artifacts.summary_path,
                'run_id': run_id,
            },
        )
    except (ValueError, LMStudioError, OSError) as exc:
        registry.update(job_id, status='failed', error=str(exc))
    except Exception as exc:  # pragma: no cover
        registry.update(job_id, status='failed', error=f'Непредвиденная ошибка: {exc}')


def compact_stage_payload(result: StageResult) -> dict[str, Any]:
    payload = result.to_dict()
    payload['status_hint'] = detect_stage_issue(payload)
    return payload


def detect_stage_issue(stage: dict[str, Any]) -> str:
    confidence = float(stage.get('confidence', 0) or 0)
    haystack = json.dumps(stage.get('deliverables', {}), ensure_ascii=False) + ' ' + str(stage.get('summary', ''))
    suspicious_markers = ['valid json', 'we need', 'continue', '???', 'json is malformed', 'the user wants json only']
    if any(marker in haystack.lower() for marker in suspicious_markers):
        return 'warning'
    if confidence < 0.65:
        return 'warning'
    return 'ok'


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def safe_run_dir(runs_root: Path, run_id: str) -> Path:
    candidate = (runs_root / run_id).resolve()
    if runs_root.resolve() not in candidate.parents:
        abort(404)
    return candidate


def discover_runs(runs_root: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not runs_root.exists():
        return []
    run_dirs = sorted([p for p in runs_root.iterdir() if p.is_dir() and p.name.startswith('run_')], key=lambda p: p.stat().st_mtime, reverse=True)
    items: list[dict[str, Any]] = []
    for run_dir in run_dirs[:limit]:
        loaded = load_run_data(run_dir, light=True)
        if loaded:
            items.append(loaded)
    return items


def load_run_data(run_dir: Path, light: bool = False) -> dict[str, Any] | None:
    results_path = run_dir / 'results.json'
    summary_path = run_dir / 'summary.txt'
    report_path = run_dir / 'report.md'
    if not results_path.exists():
        return None
    payload = json.loads(results_path.read_text(encoding='utf-8'))
    results = payload.get('results', [])
    grouped = group_results_by_block(results) if not light else []
    avg_confidence = round(mean([float(item.get('confidence', 0) or 0) for item in results]), 2) if results else 0
    low_conf_count = sum(1 for item in results if float(item.get('confidence', 0) or 0) < 0.65)
    warning_count = sum(1 for item in results if detect_stage_issue(item) == 'warning')
    final_stage = results[-1] if results else {}
    summary_text = summary_path.read_text(encoding='utf-8').strip() if summary_path.exists() else ''
    return {
        'run_id': run_dir.name,
        'run_dir': str(run_dir),
        'created_at': datetime.fromtimestamp(run_dir.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'input': payload.get('input', {}),
        'results': results,
        'blocks': grouped,
        'summary': summary_text,
        'report_preview': report_path.read_text(encoding='utf-8')[:5000] if report_path.exists() and not light else '',
        'stats': {
            'stage_count': len(results),
            'avg_confidence': avg_confidence,
            'low_conf_count': low_conf_count,
            'warning_count': warning_count,
        },
        'final_solution': final_stage.get('deliverables', {}).get('final_solution', final_stage.get('summary', '')),
        'executive_summary': final_stage.get('deliverables', {}).get('executive_summary', summary_text),
        'artifacts': {
            'report': report_path.name if report_path.exists() else '',
            'results': results_path.name,
            'summary': summary_path.name if summary_path.exists() else '',
        },
    }


def group_results_by_block(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_block = None
    current_items: list[dict[str, Any]] = []
    for item in results:
        block_name = item.get('block', 'Без блока')
        enriched = dict(item)
        enriched['status_hint'] = detect_stage_issue(enriched)
        if block_name != current_block:
            if current_block is not None:
                blocks.append({'name': current_block, 'items': current_items})
            current_block = block_name
            current_items = [enriched]
        else:
            current_items.append(enriched)
    if current_block is not None:
        blocks.append({'name': current_block, 'items': current_items})
    return blocks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='triz-agent-web',
        description='Веб-интерфейс для TRIZ Agent Studio.',
    )
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8020)
    parser.add_argument('--config', default='config/default_config.json')
    parser.add_argument('--runs-root', default='runs')
    parser.add_argument('--project-root', default='.')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args(argv)

    app = create_app(
        project_root=args.project_root,
        config_path=args.config,
        runs_root=args.runs_root,
    )
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
