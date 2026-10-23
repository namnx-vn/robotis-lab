import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation/webots/controllers/rl_h25_controller"))

from contact_evidence import ContactEvidence


class FakeContactPoint:
    def __init__(self, point, node_id):
        self.point = point
        self.node_id = node_id

    def getPoint(self):
        return self.point

    def getNodeId(self):
        return self.node_id


class ContactEvidenceTests(unittest.TestCase):
    def test_summarizes_both_feet_and_bounded_first_last_snapshots(self):
        evidence = ContactEvidence()
        names = {11: "left_ankle_roll_link", 12: "right_ankle_roll_link"}

        evidence.observe(
            [
                FakeContactPoint((-0.02, 0.0, -0.01), 11),
                FakeContactPoint((0.02, 0.0, -0.01), 12),
            ],
            names.__getitem__,
        )
        evidence.observe(
            [FakeContactPoint((0.021, 0.00001, -0.011), 12)],
            names.__getitem__,
        )

        summary = evidence.summary()
        self.assertEqual(2, summary["sample_count"])
        self.assertEqual(2, summary["samples_with_contacts"])
        self.assertEqual(1, summary["min_contact_count"])
        self.assertEqual(2, summary["max_contact_count"])
        self.assertEqual(
            ["left_ankle_roll_link", "right_ankle_roll_link"],
            summary["contact_solid_names"],
        )
        self.assertEqual(1, len(summary["last_contacts"]))
        self.assertEqual(0.0, summary["min_world_y_m"])
        self.assertEqual(0.00001, summary["max_world_y_m"])

    def test_records_samples_without_contacts(self):
        evidence = ContactEvidence()

        evidence.observe([], lambda node_id: str(node_id))

        summary = evidence.summary()
        self.assertEqual(1, summary["sample_count"])
        self.assertEqual(0, summary["samples_with_contacts"])
        self.assertEqual(0, summary["min_contact_count"])
        self.assertEqual([], summary["contact_solid_names"])
        self.assertIsNone(summary["min_world_y_m"])

    def test_rejects_nonfinite_points_and_invalid_node_identity(self):
        invalid = (
            FakeContactPoint((0.0, math.nan, 0.0), 1),
            FakeContactPoint((0.0, 0.0), 1),
            FakeContactPoint((0.0, 0.0, 0.0), True),
        )
        for point in invalid:
            with self.subTest(point=point.point, node_id=point.node_id):
                with self.assertRaises(ValueError):
                    ContactEvidence().observe([point], lambda node_id: "foot")

    def test_rejects_empty_solid_name(self):
        with self.assertRaises(ValueError):
            ContactEvidence().observe(
                [FakeContactPoint((0.0, 0.0, 0.0), 1)], lambda node_id: ""
            )


if __name__ == "__main__":
    unittest.main()
