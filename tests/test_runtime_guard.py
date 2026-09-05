import unittest
from unittest.mock import patch

from triz_agent.runtime_guard import GpuSnapshot, RuntimeGuardError, enforce_runtime_guard


class RuntimeGuardTest(unittest.TestCase):
    @patch('triz_agent.runtime_guard.query_nvidia_smi')
    def test_allows_snapshot_under_limits(self, query):
        query.return_value = [GpuSnapshot(0, 'GPU', 70.0, 90.0, 8000.0, 12000.0, 200.0)]
        snapshots = enforce_runtime_guard(max_gpu_temp_c=80.0, max_vram_pct=90.0)
        self.assertEqual(len(snapshots), 1)

    @patch('triz_agent.runtime_guard.query_nvidia_smi')
    def test_blocks_temperature_limit(self, query):
        query.return_value = [GpuSnapshot(0, 'GPU', 82.0, 90.0, 8000.0, 12000.0, 200.0)]
        with self.assertRaises(RuntimeGuardError):
            enforce_runtime_guard(max_gpu_temp_c=80.0)

    @patch('triz_agent.runtime_guard.query_nvidia_smi')
    def test_blocks_vram_limit(self, query):
        query.return_value = [GpuSnapshot(0, 'GPU', 70.0, 90.0, 11500.0, 12000.0, 200.0)]
        with self.assertRaises(RuntimeGuardError):
            enforce_runtime_guard(max_vram_pct=95.0)


if __name__ == '__main__':
    unittest.main()
