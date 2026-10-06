"""Checks of preservation rejection, renderer invariants and budget candidates."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np

path = Path(__file__).resolve().parents[1]/'scripts/response_retrieval_pilot.py'
spec = importlib.util.spec_from_file_location('pilot', path)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class PilotTests(unittest.TestCase):
    def test_selection_rejects_high_score_with_side_effects(self):
        base = dict(z=pilot.BASE.tolist(), margin=0., centroid=1000., accents=[1/np.sqrt(8)]*8)
        acceptable = dict(base, z=(pilot.BASE+[0, -.1, 0, 0]).tolist(), margin=.03)
        bad_timbre = dict(acceptable, centroid=1500., margin=.9)
        bad_accent = dict(acceptable, accents=[1., 0, 0, 0, 0, 0, 0, 0], margin=.95)
        too_many = dict(acceptable, z=(pilot.BASE+[.1, .1, .1, 0]).tolist(), margin=.99)
        self.assertIs(pilot.select_result([base, acceptable, bad_timbre, bad_accent, too_many]), acceptable)
        self.assertIs(pilot.select_result([base, bad_timbre, bad_accent, too_many]), base)

    def test_score_pitches_onsets_and_accents_survive_edits(self):
        passage = pilot.PASSAGES['query_a']
        def events(z):
            lines = [s.split() for s in pilot.csd_text(passage, z).splitlines() if s.startswith('i1 ')]
            return [(s[1], s[3], s[4]) for s in lines]
        baseline = events(pilot.BASE)
        self.assertEqual(len(baseline), 8)
        for j in range(4):
            for sign in (-1, 1):
                self.assertEqual(events(pilot.BASE+sign*.25*np.eye(4)[j]), baseline)

    def test_local_proposals_respect_edit_limits(self):
        rng = np.random.default_rng(123)
        for _ in range(10):
            proposals = pilot.local_search(rng.normal(size=(10, 4)), 8)
            self.assertEqual(len(proposals), 8)
            self.assertTrue(all(pilot.allowed(d) for d in proposals))
            self.assertEqual(len({tuple(d) for d in proposals}), 8)

    def test_invalid_controls_are_rejected(self):
        for controls in ([np.nan, 0, 0, 0], [1.1, 0, 0, 0], [0, 0, 0]):
            with self.assertRaises(ValueError):
                pilot.parameters(controls)

    def test_response_matching_can_override_donor_text_fit(self):
        base = dict(embedding=[1., 0.], margin=0., centroid=1000., accents=[1/np.sqrt(8)]*8)
        bank = []
        for j, margin, slope in [(1, .1, 100.), (3, .08, 0.)]:
            delta = -.2*np.eye(4)[j]
            jd = np.zeros((10, 4))
            jd[:, j] = slope
            bank.append(dict(delta=delta.tolist(), base=base, edited=dict(base, margin=margin),
                             jacobian=jd.tolist()))
        ordinary = pilot.retrieve(bank, base, None, 1, False)[0]
        matched = pilot.retrieve(bank, base, np.zeros((10, 4)), 1, True, transport=False)[0]
        self.assertEqual(np.flatnonzero(ordinary).tolist(), [1])
        self.assertEqual(np.flatnonzero(matched).tolist(), [3])


if __name__ == '__main__':
    unittest.main()
