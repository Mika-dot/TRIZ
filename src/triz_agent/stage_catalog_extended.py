from __future__ import annotations

from typing import Dict, Iterable, List

from triz_agent.models import StageSpec
from triz_agent.stage_catalog import STAGES as CORE_STAGES


def _stage(
    stage_id: str,
    block: str,
    title: str,
    purpose: str,
    fields: Iterable[str],
    checks: Iterable[str],
) -> StageSpec:
    return StageSpec(
        id=stage_id,
        block=block,
        title=title,
        purpose=purpose,
        required_fields={name: name.replace('_', ' ') for name in fields},
        quality_checks=list(checks),
    )


FSA_STAGES = [
    _stage('10.1', 'Блок 10. ФСА', 'Компонентная модель',
           'Построй компонентную модель: система, подсистемы, надсистема, целевой объект и носители функций.',
           ['components', 'supersystem_components', 'target_component', 'component_assumptions'],
           ['Границы системы заданы явно', 'Компоненты не подменены абстрактными свойствами']),
    _stage('10.2', 'Блок 10. ФСА', 'Функциональная модель',
           'Опиши функции как носитель → действие → объект; раздели полезные, вредные, нейтральные и отсутствующие взаимодействия.',
           ['function_table', 'useful_functions', 'harmful_functions', 'missing_functions'],
           ['Функции сформулированы как действия', 'Полезные и вредные функции не смешаны']),
    _stage('10.3', 'Блок 10. ФСА', 'Качество функций',
           'Оцени функции как достаточные, недостаточные или избыточные и выдели функциональные недостатки.',
           ['function_performance', 'insufficient_functions', 'excessive_functions', 'functional_disadvantages'],
           ['Оценка привязана к критериям успеха', 'Неизвестные значения отмечены как неизвестные']),
    _stage('10.4', 'Блок 10. ФСА', 'Стоимость функций',
           'Свяжи компоненты и функции с деньгами, compute, VRAM/RAM, latency, energy, сложностью и эксплуатационным риском.',
           ['cost_dimensions', 'component_cost_map', 'function_cost_map', 'cost_uncertainty'],
           ['Численные затраты без данных не выдумываются', 'Для SLM учитываются runtime-ресурсы']),
    _stage('10.5', 'Блок 10. ФСА', 'Value map и trimming',
           'Найди низкоценные/дорогие компоненты и кандидатов на удаление, объединение или перенос функций.',
           ['value_map', 'low_value_components', 'trimming_candidates', 'trimming_risks'],
           ['Главная полезная функция сохраняется', 'Высокая стоимость сама по себе не означает удалить компонент']),
    _stage('10.6', 'Блок 10. ФСА', 'Перепроектирование',
           'Сформируй варианты переноса/объединения функций и план проверки роста ценности.',
           ['fsa_redesigns', 'function_reassignment', 'expected_savings', 'fsa_validation_plan'],
           ['Экономия причинно связана с изменением', 'Обязательные функции и ограничения сохранены']),
]


ARIZ_STAGES = [
    _stage('11.1', 'Блок 11. АРИЗ-85C', 'Часть 1 — анализ задачи',
           'Сформируй конфликтующую пару, варианты технического противоречия, усили конфликт и задай мини-задачу с минимальными изменениями.',
           ['conflicting_elements', 'technical_contradiction_variants', 'intensified_conflict', 'ariz_mini_problem'],
           ['Мини-задача не содержит готового решения', 'Конфликт не подменяет исходную цель']),
    _stage('11.2', 'Блок 11. АРИЗ-85C', 'Часть 2 — модель задачи',
           'Зафиксируй оперативную зону, оперативное время и вещественно-полевые ресурсы зоны, системы и надсистемы.',
           ['operational_zone', 'operational_time', 'substance_field_resources', 'resource_priority'],
           ['Ресурсы связаны с ОЗ/ОВ', 'Сначала используются внутренние ресурсы']),
    _stage('11.3', 'Блок 11. АРИЗ-85C', 'Часть 3 — ИКР-1 и ФП',
           'Сформулируй ИКР-1 через X-элемент и макро-/микрофизическое противоречие.',
           ['ifr_1', 'x_element', 'macro_physical_contradiction', 'micro_physical_contradiction'],
           ['ИКР не подменен конструкцией', 'ФП относится к одному параметру/состоянию']),
    _stage('11.4', 'Блок 11. АРИЗ-85C', 'Часть 4 — мобилизация ресурсов',
           'Используй внутренние, производные, временные, пространственные и микроуровневые ресурсы до добавления новых сущностей.',
           ['mobilized_resources', 'derived_resources', 'micro_level_model', 'resource_solution_hypotheses'],
           ['Не добавляются дорогие сущности без необходимости', 'Гипотезы связаны с ФП']),
    _stage('11.5', 'Блок 11. АРИЗ-85C', 'Часть 5 — информационный фонд',
           'Примени стандарты, эффекты, принципы и способы разделения только после построения модели конфликта.',
           ['standard_solution_candidates', 'effect_candidates', 'principle_candidates', 'candidate_mechanisms'],
           ['Инструменты выбраны по модели задачи', 'Неизвестные номера стандартов не выдумываются']),
    _stage('11.6', 'Блок 11. АРИЗ-85C', 'Часть 6 — переформулирование',
           'При слабом решении смени системный уровень/конфликтующую пару и укажи, с какого шага повторить анализ.',
           ['solution_status', 'reformulation_options', 'system_level_shift', 'restart_recommendation'],
           ['Исходная потребность сохраняется', 'Возврат в цикл имеет конкретную причину']),
    _stage('11.7', 'Блок 11. АРИЗ-85C', 'Часть 7 — проверка снятия ФП',
           'Проверь, реально ли механизм устраняет физическое противоречие, приближает к ИКР и не является скрытым компромиссом.',
           ['physical_contradiction_resolution', 'compromise_check', 'ideality_gain', 'new_conflicts'],
           ['Проверен механизм, а не формулировка', 'Новые вредные эффекты перечислены']),
    _stage('11.8', 'Блок 11. АРИЗ-85C', 'Часть 8 — развитие решения',
           'Исследуй влияние на надсистему, масштабирование, перенос принципа и дальнейшие линии развития.',
           ['supersystem_effects', 'generalization', 'transfer_cases', 'evolution_paths'],
           ['Учтены вторичные эффекты', 'Обобщение связано с механизмом']),
    _stage('11.9', 'Блок 11. АРИЗ-85C', 'Часть 9 — аудит хода решения',
           'Сопоставь реальный ход решения с АРИЗ, выдели отклонения, слабые допущения и повторно используемые эвристики.',
           ['ariz_trace', 'deviations', 'weak_reasoning_points', 'reusable_heuristics'],
           ['Данные отделены от гипотез', 'Отмечены места для эксперимента/внешней проверки']),
]


SLM_ARCHITECTURE_STAGES = [
    _stage('12.1', 'Блок 12. Архитектура SLM', 'Бюджет модели и памяти',
           'Разложи лимит малой LLM на веса, quantization, KV-cache, context, buffers, CPU/RAM offload и VRAM reserve.',
           ['weight_budget', 'kv_cache_budget', 'ram_vram_budget', 'memory_experiments'],
           ['Размер файла весов не равен автоматически VRAM', 'Неизмеренные числа отмечены как оценки']),
    _stage('12.2', 'Блок 12. Архитектура SLM', 'Декомпозиция и routing',
           'Раздели задачи между основной моделью, specialist model, правилом, tool/API и fallback.',
           ['task_classes', 'routing_policy', 'specialist_candidates', 'fallback_policy'],
           ['Routing повышает качество или снижает цену', 'Не создается бессмысленная многоагентность']),
    _stage('12.3', 'Блок 12. Архитектура SLM', 'Решение о RAG',
           'Определи, где нужен retrieval, где достаточно модели, где нужен tool/API и где правильнее abstain.',
           ['rag_required_for', 'no_rag_for', 'knowledge_sources', 'freshness_policy'],
           ['RAG не включается автоматически', 'Определены доверие и актуальность источников']),
    _stage('12.4', 'Блок 12. Архитектура SLM', 'Retrieval и rerank',
           'Спроектируй query transformation, sparse/dense/hybrid/graph retrieval, filters, reranking и retrieval metrics.',
           ['query_transform', 'retrieval_strategy', 'rerank_strategy', 'retrieval_metrics'],
           ['Retrieval metrics отделены от generation quality', 'Rerank имеет измеримую цель']),
    _stage('12.5', 'Блок 12. Архитектура SLM', 'Context packing и grounding',
           'Определи chunking, deduplication, packing, citation policy и обработку противоречивых источников.',
           ['chunking_policy', 'context_packing', 'citation_policy', 'conflict_resolution'],
           ['Контекст не переполняется мусором', 'Источник поддерживает именно соответствующее утверждение']),
    _stage('12.6', 'Блок 12. Архитектура SLM', 'Tools и structured output',
           'Передай вычисления, БД, код и проверяемые действия детерминированным инструментам; задай JSON/schema contracts.',
           ['tool_candidates', 'schema_contracts', 'validation_rules', 'tool_failure_policy'],
           ['Инструменты валидируют вход/выход', 'LLM не заменяет БД/калькулятор без причины']),
    _stage('12.7', 'Блок 12. Архитектура SLM', 'Память и агентность',
           'Определи необходимость short/long-term memory и agent loop; задай TTL, budget, step/token/time limits.',
           ['memory_layers', 'write_policy', 'agent_loop', 'stop_conditions'],
           ['Память не превращается в бесконтрольный контекст', 'У agent loop есть жесткие stop conditions']),
]


RELIABILITY_STAGES = [
    _stage('13.1', 'Блок 13. Надежность', 'Декомпозиция на claims',
           'Раздели ответ на входные данные, выводы, факты, прогнозы и рекомендации; определи требуемый уровень evidence.',
           ['claim_types', 'verification_required', 'evidence_requirements', 'unsupported_claim_policy'],
           ['Мнение модели не является доказательством', 'Высокорисковые факты проверяются строже']),
    _stage('13.2', 'Блок 13. Надежность', 'Evidence coverage',
           'Проверь полноту доказательств, конфликты источников и поведение при отсутствующем evidence.',
           ['evidence_coverage_metric', 'contradiction_detection', 'missing_evidence_behavior', 'source_priority'],
           ['Нет retrieval — нет выдуманного факта', 'Противоречия источников не скрываются']),
    _stage('13.3', 'Блок 13. Надежность', 'Независимый verifier',
           'Выбери rule/NLI/fact-check/second-model/retrieval verifier и путь исправления проваленной проверки.',
           ['verifier_architecture', 'independence_level', 'verification_cost', 'correction_path'],
           ['Self-reflection не считается полностью независимым verifier', 'Цена проверки соответствует риску']),
    _stage('13.4', 'Блок 13. Надежность', 'Abstention и escalation',
           'Задай наблюдаемые confidence signals, условия отказа, дополнительного retrieval/tool и эскалации.',
           ['confidence_signals', 'abstention_rules', 'escalation_rules', 'calibration_plan'],
           ['Самооценка LLM не равна калиброванной вероятности', 'Правильный отказ допустим']),
    _stage('13.5', 'Блок 13. Надежность', 'Adversarial/failure tests',
           'Тестируй prompt injection, ложный/противоречивый контекст, несуществующие сущности и провокацию на выдумывание.',
           ['attack_cases', 'expected_safe_behavior', 'failure_metrics', 'regression_corpus'],
           ['Тесты имеют ожидаемый результат', 'Failure cases попадают в regression corpus']),
    _stage('13.6', 'Блок 13. Надежность', 'Evaluation gates',
           'Определи release gates для task quality, factuality, retrieval, abstention, latency, memory и stability.',
           ['quality_metrics', 'rag_metrics', 'runtime_metrics', 'release_gates'],
           ['Метрики привязаны к задачам', 'Средние значения не скрывают критические failure cases']),
]


RUNTIME_STAGES = [
    _stage('14.1', 'Блок 14. Runtime', 'VRAM/RAM/KV-cache',
           'Построй фактический memory budget для idle/prefill/decode/max-context/batch/concurrency и запас до OOM.',
           ['memory_modes', 'kv_growth', 'oom_margin', 'memory_controls'],
           ['Используются измерения или явные оценки', 'Есть запас до OOM']),
    _stage('14.2', 'Блок 14. Runtime', 'Latency/throughput/power',
           'Раздели TTFT, prefill, decode, E2E, tokens/s, requests/s, utilization и power.',
           ['latency_profile', 'throughput_profile', 'power_profile', 'bottleneck_hypothesis'],
           ['Prefill и decode не смешаны', 'Bottleneck подтверждается профилированием']),
    _stage('14.3', 'Блок 14. Runtime', 'Thermal limits и throttling',
           'Используй vendor-specific пределы и измерь temperature/frequency/utilization во времени для поиска throttling.',
           ['vendor_limits', 'observed_thermal_curve', 'throttling_signals', 'thermal_unknowns'],
           ['Нет универсальных выдуманных температур', 'Лимиты относятся к конкретному железу']),
    _stage('14.4', 'Блок 14. Runtime', 'Адаптивная runtime-политика',
           'Спроектируй мягкую деградацию: context cap, concurrency, batch, quant/model routing, speculative decoding/offload.',
           ['runtime_signals', 'degradation_levels', 'control_actions', 'recovery_rules'],
           ['Политика не осциллирует без hysteresis/window', 'Качество деградирует контролируемо']),
    _stage('14.5', 'Блок 14. Runtime', 'Soak/stress test',
           'Спроектируй длительный прогон для нагрева, memory leak, throughput drift, queue growth и редких ошибок.',
           ['soak_scenarios', 'telemetry', 'failure_thresholds', 'post_test_checks'],
           ['Проверяется длительная нагрузка', 'Есть stop/acceptance criteria']),
]


FINAL_SLM_STAGES = [
    _stage('15.1', 'Блок 15. Синтез SLM', 'Парето-набор архитектур',
           'Собери недоминируемые варианты по quality, memory, latency, reliability и complexity.',
           ['architecture_candidates', 'pareto_axes', 'dominated_options', 'pareto_front'],
           ['Сравнение многокритериальное', 'Неизмеренные показатели не выдаются за точные']),
    _stage('15.2', 'Блок 15. Синтез SLM', 'План экспериментов',
           'Преобразуй спорные решения в A/B experiments с hypothesis, baseline, metric и stop criterion.',
           ['experiments', 'baselines', 'success_thresholds', 'experiment_order'],
           ['Эксперименты различают гипотезы', 'Есть baseline']),
    _stage('15.3', 'Блок 15. Синтез SLM', 'Observability и rollback',
           'Версионируй model/prompt/index/config, логируй trace и задай alerts/rollback.',
           ['observability_fields', 'versioned_artifacts', 'alerts', 'rollback_plan'],
           ['Плохой ответ воспроизводим', 'Rollback не зависит от угадывания причины']),
    _stage('15.4', 'Блок 15. Синтез SLM', 'Итоговая system card',
           'Собери итоговую архитектуру, ИКР, противоречия, функции, RAG/verifier/runtime policy, ограничения и deployment checklist.',
           ['selected_architecture', 'why_it_wins', 'known_limits', 'deployment_checklist'],
           ['Финал опирается на предыдущие этапы', 'Границы применимости указаны явно']),
]


TRIZ_FULL_STAGES: List[StageSpec] = list(CORE_STAGES) + FSA_STAGES + ARIZ_STAGES
SLM_FULL_STAGES: List[StageSpec] = (
    TRIZ_FULL_STAGES + SLM_ARCHITECTURE_STAGES + RELIABILITY_STAGES + RUNTIME_STAGES + FINAL_SLM_STAGES
)

STAGE_PROFILES: Dict[str, List[StageSpec]] = {
    'core': list(CORE_STAGES),
    'triz_full': TRIZ_FULL_STAGES,
    'slm_full': SLM_FULL_STAGES,
    'full': SLM_FULL_STAGES,
}


def get_stages(profile: str = 'slm_full') -> List[StageSpec]:
    key = (profile or 'slm_full').strip().lower()
    if key not in STAGE_PROFILES:
        allowed = ', '.join(sorted(STAGE_PROFILES))
        raise ValueError(f'Unknown pipeline_profile={profile!r}. Allowed: {allowed}')
    return list(STAGE_PROFILES[key])


EXTENDED_STAGE_INDEX = {stage.id: stage for stage in SLM_FULL_STAGES}
