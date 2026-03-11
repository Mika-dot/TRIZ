import unittest

from triz_agent.stage_catalog import STAGES


class StageCatalogTest(unittest.TestCase):
    def test_stage_count(self):
        self.assertEqual(len(STAGES), 40)

    def test_each_stage_has_required_fields(self):
        for stage in STAGES:
            self.assertTrue(stage.required_fields)
            self.assertTrue(stage.quality_checks)


if __name__ == '__main__':
    unittest.main()
