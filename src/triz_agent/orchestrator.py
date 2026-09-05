from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Protocol

from triz_agent.config import AppConfig
from triz_agent.models import PipelineInput, RunArtifacts, StageResult
from triz_agent.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from triz_agent.reporting import ensure_run_dir, save_run_artifacts, save_stage_log
from triz_agent.runtime_guard import enforce_runtime_guard
from triz_agent.stage_catalog_extended import get_stages


class LLMClientProtocol(Protocol):
    def call_stage(self, stage, model: str, system_prompt: str, user_prompt: str):
        ...


ProgressCallback = Callable[[int, int, object, StageResult, str], None]


@dataclass
class OrchestrationOutput:
    results: List[StageResult]
    artifacts: RunArtifacts


class TrizOrchestrator:
    def __init__(self, config: AppConfig, client: LLMClientProtocol):
        self.config = config
        self.client = client

    def run(
        self,
        pipeline_input: PipelineInput,
        output_root: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> OrchestrationOutput:
        output_base = output_root or self.config.output_root
        run_dir = ensure_run_dir(output_base)
        results: List[StageResult] = []
        stages = get_stages(self.config.pipeline_profile)
        total_stages = len(stages)

        for index, stage in enumerate(stages):
            if self.config.runtime_guard_enabled:
                enforce_runtime_guard(
                    max_gpu_temp_c=self.config.runtime_guard_max_gpu_temp_c,
                    max_vram_pct=self.config.runtime_guard_max_vram_pct,
                )

            model = self.config.pick_model(stage.id, index)
            user_prompt = build_user_prompt(
                stage=stage,
                pipeline_input=pipeline_input,
                prior_results=results,
                max_context_chars=self.config.max_context_chars,
            )
            result, request_payload, raw_content = self.client.call_stage(
                stage=stage,
                model=model,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            results.append(result)
            save_stage_log(
                run_dir=Path(run_dir),
                result=result,
                request_payload=request_payload,
                raw_content=raw_content,
            )
            if progress_callback:
                progress_callback(index + 1, total_stages, stage, result, str(run_dir))

        artifacts = save_run_artifacts(
            run_dir=Path(run_dir),
            pipeline_input=pipeline_input,
            results=results,
        )
        return OrchestrationOutput(results=results, artifacts=artifacts)
