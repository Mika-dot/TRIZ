import unittest

from triz_agent.stage_catalog_extended import get_stages


class ExtendedStageCatalogTest(unittest.TestCase):
    def test_profiles_have_expected_sizes(self):
        self.assertEqual(len(get_stages('core')), 40)
        self.assertEqual(len(get_stages('triz_full')), 55)
        self.assertEqual(len(get_stages('slm_full')), 77)
        self.assertEqual(len(get_stages('full')), 77)

    def test_stage_ids_are_unique(self):
        ids = [stage.id for stage in get_stages('slm_full')]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields_and_checks_exist(self):
        for stage in get_stages('slm_full'):
            self.assertTrue(stage.required_fields)
            self.assertTrue(stage.quality_checks)

    def test_unknown_profile_fails_fast(self):
        with self.assertRaises(ValueError):
            get_stages('does-not-exist')


if __name__ == '__main__':
    unittest.main()
