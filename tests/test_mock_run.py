import tempfile
import unittest
from pathlib import Path

from triz_agent.config import AppConfig
from triz_agent.mock_client import MockLLMClient
from triz_agent.models import PipelineInput
from triz_agent.orchestrator import TrizOrchestrator


class MockRunTest(unittest.TestCase):
    def test_mock_pipeline_generates_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(output_root=tmp_dir, default_model='mock-model')
            orchestrator = TrizOrchestrator(config=config, client=MockLLMClient())
            output = orchestrator.run(
                PipelineInput(problem='Тестовая задача по снижению перегрева оборудования.'),
                output_root=tmp_dir,
            )
            self.assertEqual(len(output.results), 40)
            self.assertTrue(Path(output.artifacts.report_path).exists())
            self.assertTrue(Path(output.artifacts.json_path).exists())
            self.assertTrue(Path(output.artifacts.summary_path).exists())


if __name__ == '__main__':
    unittest.main()
