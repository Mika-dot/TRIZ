# Evaluation framework

Цель evaluation — не получить один «LLM score», а доказать, что новая архитектура лучше по конкретным функциям и ограничениям.

| Контур | Метрики |
|---|---|
| Task quality | exact match / F1 / pass@k / domain rubric / human pairwise |
| Factuality | unsupported claim rate, grounded claim rate, contradiction rate |
| RAG retrieval | Recall@k, hit rate, MRR, nDCG, rerank lift |
| Abstention | precision/recall/F1 на answerable vs unanswerable |
| Latency | TTFT, decode latency, E2E p50/p95/p99 |
| Throughput | tokens/s, requests/s, queue depth |
| Memory | peak VRAM, peak RAM, KV-cache growth, OOM rate |
| Stability | error rate, restart rate, performance drift during soak |
| Thermal | temperature, clock throttling, power draw over time |
| Cost | energy/request, hardware utilization, engineering complexity |

## Правила сравнения

1. Зафиксировать baseline.
2. Менять одну архитектурную переменную за эксперимент, если возможно.
3. Использовать одинаковый corpus и одинаковые запросы.
4. Разделять retrieval failure и generation failure.
5. Сохранять версии model, quantization, prompt, index и config.
6. Не ограничиваться средним значением: смотреть критические failure cases и хвосты latency.
7. Отдельно тестировать запросы, на которые система должна отказаться отвечать.
8. Каждый серьезный найденный сбой добавлять в regression set.

## Release gate

Архитектура готова к пилоту только если одновременно проходит заданные пороги task quality/factuality/abstention, укладывается в VRAM/RAM budget с запасом, не имеет OOM/restart в soak test, выполняет SLA по p95 latency и не уходит в устойчивый thermal/power throttling на целевом устройстве.

Конкретные пороги определяются приложением и измерениями, а не генерируются LLM.
