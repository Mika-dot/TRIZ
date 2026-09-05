from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
from typing import List, Optional


@dataclass(frozen=True)
class GpuSnapshot:
    index: int
    name: str
    temperature_c: float
    utilization_pct: float
    memory_used_mb: float
    memory_total_mb: float
    power_w: Optional[float] = None

    @property
    def memory_used_pct(self) -> float:
        if self.memory_total_mb <= 0:
            return 0.0
        return 100.0 * self.memory_used_mb / self.memory_total_mb


class RuntimeGuardError(RuntimeError):
    pass


def _parse_optional_float(value: str) -> Optional[float]:
    value = value.strip()
    if not value or value.lower() in {'n/a', '[n/a]', 'not supported'}:
        return None
    return float(value)


def query_nvidia_smi() -> List[GpuSnapshot]:
    exe = shutil.which('nvidia-smi')
    if not exe:
        raise RuntimeGuardError('runtime_guard enabled, but nvidia-smi was not found on this host')
    query = 'index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw'
    completed = subprocess.run(
        [exe, f'--query-gpu={query}', '--format=csv,noheader,nounits'],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or 'unknown nvidia-smi error'
        raise RuntimeGuardError(f'nvidia-smi failed: {message}')
    snapshots: List[GpuSnapshot] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(',')]
        if len(parts) != 7:
            raise RuntimeGuardError(f'unexpected nvidia-smi output: {line!r}')
        snapshots.append(GpuSnapshot(
            index=int(parts[0]), name=parts[1], temperature_c=float(parts[2]),
            utilization_pct=float(parts[3]), memory_used_mb=float(parts[4]),
            memory_total_mb=float(parts[5]), power_w=_parse_optional_float(parts[6]),
        ))
    return snapshots


def enforce_runtime_guard(*, max_gpu_temp_c: Optional[float] = None, max_vram_pct: Optional[float] = None) -> List[GpuSnapshot]:
    snapshots = query_nvidia_smi()
    violations: List[str] = []
    for gpu in snapshots:
        if max_gpu_temp_c is not None and gpu.temperature_c >= max_gpu_temp_c:
            violations.append(f'GPU {gpu.index} {gpu.name}: {gpu.temperature_c:.1f}C >= {max_gpu_temp_c:.1f}C')
        if max_vram_pct is not None and gpu.memory_used_pct >= max_vram_pct:
            violations.append(f'GPU {gpu.index} {gpu.name}: VRAM {gpu.memory_used_pct:.1f}% >= {max_vram_pct:.1f}%')
    if violations:
        raise RuntimeGuardError('runtime guard blocked next LLM stage: ' + '; '.join(violations))
    return snapshots
