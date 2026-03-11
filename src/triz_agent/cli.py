from __future__ import annotations

import argparse
import sys
from pathlib import Path

from triz_agent.config import AppConfig
from triz_agent.llm_client import LMStudioClient, LMStudioError
from triz_agent.mock_client import MockLLMClient
from triz_agent.models import PipelineInput
from triz_agent.orchestrator import TrizOrchestrator


def read_optional_file(path: str | None) -> str:
    if not path:
        return ''
    return Path(path).read_text(encoding='utf-8')


def build_pipeline_input(args: argparse.Namespace) -> PipelineInput:
    problem = args.problem or read_optional_file(args.problem_file)
    if not problem.strip():
        raise ValueError('Нужно передать --problem или --problem-file.')
    constraints = args.constraints or read_optional_file(args.constraints_file)
    context_notes = args.context_notes or read_optional_file(args.context_notes_file)
    return PipelineInput(problem=problem, constraints=constraints, context_notes=context_notes)


def cmd_list_models(args: argparse.Namespace) -> int:
    config = AppConfig.from_file(args.config)
    client = LMStudioClient(config)
    try:
        models = client.list_models()
    except Exception as exc:
        print(f'Ошибка доступа к LM Studio: {exc}', file=sys.stderr)
        return 2
    if not models:
        print('LM Studio доступен, но не вернул загруженных моделей.')
        return 0
    print('Доступные модели:')
    for model in models:
        print(f'- {model}')
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = AppConfig.from_file(args.config)
    pipeline_input = build_pipeline_input(args)
    client = MockLLMClient() if args.mock else LMStudioClient(config)
    orchestrator = TrizOrchestrator(config=config, client=client)

    try:
        output = orchestrator.run(pipeline_input=pipeline_input, output_root=args.output_root)
    except (ValueError, LMStudioError, OSError) as exc:
        print(f'Ошибка выполнения пайплайна: {exc}', file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f'Непредвиденная ошибка: {exc}', file=sys.stderr)
        return 3

    print('Пайплайн завершен.')
    print(f'Каталог запуска: {output.artifacts.run_dir}')
    print(f'Отчет: {output.artifacts.report_path}')
    print(f'JSON: {output.artifacts.json_path}')
    print(f'Краткое summary: {output.artifacts.summary_path}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='triz-agent',
        description='Полный ТРИЗ/АРИЗ-пайплайн с независимыми stateless-вызовами LM Studio на каждом этапе.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    list_models = subparsers.add_parser('list-models', help='Показать модели, доступные через LM Studio.')
    list_models.add_argument('--config', default='config/default_config.json', help='Путь к JSON-конфигу.')
    list_models.set_defaults(func=cmd_list_models)

    run = subparsers.add_parser('run', help='Запустить полный пайплайн ТРИЗ.')
    run.add_argument('--config', default='config/default_config.json', help='Путь к JSON-конфигу.')
    run.add_argument('--problem', help='Текст задачи.')
    run.add_argument('--problem-file', help='Путь к файлу с задачей.')
    run.add_argument('--constraints', help='Ограничения в виде текста.')
    run.add_argument('--constraints-file', help='Путь к файлу с ограничениями.')
    run.add_argument('--context-notes', help='Дополнительный контекст в виде текста.')
    run.add_argument('--context-notes-file', help='Путь к файлу с дополнительным контекстом.')
    run.add_argument('--output-root', default='runs', help='Каталог для результатов.')
    run.add_argument('--mock', action='store_true', help='Демонстрационный режим без вызовов LM Studio.')
    run.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
