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
    FOOT_IDS = {"left": 11, "right": 12}

    @staticmethod
    def support_contacts():
        return [
            FakeContactPoint((-0.05, 0.0, -0.02), 11),
            FakeContactPoint((-0.05, 0.0, 0.02), 11),
            FakeContactPoint((-0.01, 0.0, -0.02), 11),
            FakeContactPoint((-0.01, 0.0, 0.02), 11),
            FakeContactPoint((0.01, 0.0, -0.02), 12),
            FakeContactPoint((0.01, 0.0, 0.02), 12),
            FakeContactPoint((0.05, 0.0, -0.02), 12),
            FakeContactPoint((0.05, 0.0, 0.02), 12),
        ]

    def test_summarizes_both_feet_and_bounded_first_last_snapshots(self):
        evidence = ContactEvidence()

        evidence.observe(
            [
                FakeContactPoint((-0.02, 0.0, -0.01), 11),
                FakeContactPoint((0.02, 0.0, -0.01), 12),
            ],
        )
        evidence.observe(
            [FakeContactPoint((0.021, 0.00001, -0.011), 12)],
        )

        summary = evidence.summary()
        self.assertEqual(2, summary["sample_count"])
        self.assertEqual(2, summary["samples_with_contacts"])
        self.assertEqual(1, summary["min_contact_count"])
        self.assertEqual(2, summary["max_contact_count"])
        self.assertEqual(
            [11, 12],
            summary["contact_solid_node_ids"],
        )
        self.assertEqual(
            {"11": 1, "12": 2},
            summary["samples_by_solid_node_id"],
        )
        self.assertEqual(1, len(summary["last_contacts"]))
        self.assertEqual(0.0, summary["min_world_y_m"])
        self.assertEqual(0.00001, summary["max_world_y_m"])

    def test_records_samples_without_contacts(self):
        evidence = ContactEvidence()

        evidence.observe([])

        summary = evidence.summary()
        self.assertEqual(1, summary["sample_count"])
        self.assertEqual(0, summary["samples_with_contacts"])
        self.assertEqual(0, summary["min_contact_count"])
        self.assertEqual([], summary["contact_solid_node_ids"])
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
                    ContactEvidence().observe([point])

    def test_explicit_foot_nodes_produce_support_sample_and_positive_margin(self):
        evidence = ContactEvidence(self.FOOT_IDS)

        sample = evidence.observe(
            self.support_contacts(),
            com_world_m=(0.0, 0.12, 0.0),
            foot_positions_world_m={
                "left": (-0.03, 0.009, -0.008),
                "right": (0.03, 0.009, -0.008),
            },
        )

        self.assertEqual({"left": True, "right": True}, sample["contacts_by_foot"])
        self.assertEqual({"left": 4, "right": 4}, sample["contact_counts_by_foot"])
        self.assertEqual(
            {
                "left": [-0.03, 0.009, -0.008],
                "right": [0.03, 0.009, -0.008],
            },
            sample["foot_positions_world_m"],
        )
        self.assertEqual(4, len(sample["support_polygon_xz_m"]))
        self.assertAlmostEqual(0.02, sample["com_support_margin_m"])

        summary = evidence.summary()
        self.assertEqual("solid_node_id", summary["foot_mapping"])
        self.assertEqual(self.FOOT_IDS, summary["foot_node_ids"])
        self.assertEqual(sample, summary["last_sample"])

    def test_world_x_mapping_uses_root_position_for_per_foot_counts(self):
        evidence = ContactEvidence("world_x_sign")

        sample = evidence.observe(
            [
                FakeContactPoint((0.08, 0.0, 0.0), 11),
                FakeContactPoint((0.12, 0.0, 0.0), 12),
            ],
            root_x_m=0.10,
            com_world_m=(0.10, 0.12, 0.0),
            foot_positions_world_m={
                "left": (0.08, 0.009, 0.0),
                "right": (0.12, 0.009, 0.0),
            },
        )

        self.assertEqual({"left": True, "right": True}, sample["contacts_by_foot"])
        self.assertEqual({"left": 1, "right": 1}, sample["contact_counts_by_foot"])

    def test_support_margin_is_negative_when_com_projection_is_outside(self):
        evidence = ContactEvidence(self.FOOT_IDS)

        sample = evidence.observe(
            self.support_contacts(),
            com_world_m=(0.08, 0.12, 0.0),
            foot_positions_world_m={
                "left": (-0.03, 0.009, -0.008),
                "right": (0.03, 0.009, -0.008),
            },
        )

        self.assertLess(sample["com_support_margin_m"], 0.0)

    def test_explicit_foot_mapping_rejects_invalid_mapping_and_retains_other_contacts(self):
        for mapping in (
            {"left": 11, "right": 11},
            {"left": 11},
            {"left": True, "right": 12},
            {"left": 0, "right": 12},
        ):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                ContactEvidence(mapping)

        evidence = ContactEvidence(self.FOOT_IDS)
        sample = evidence.observe(
            [FakeContactPoint((0.0, 0.0, 0.0), 99)],
            com_world_m=(0.0, 0.12, 0.0),
            foot_positions_world_m={
                "left": (-0.03, 0.009, -0.008),
                "right": (0.03, 0.009, -0.008),
            },
        )
        self.assertEqual([99], sample["unexpected_contact_solid_node_ids"])
        self.assertEqual({"left": False, "right": False}, sample["contacts_by_foot"])
        self.assertEqual([], sample["support_polygon_xz_m"])
        self.assertIsNone(sample["com_support_margin_m"])

    def test_returned_sample_and_summary_are_detached(self):
        evidence = ContactEvidence(self.FOOT_IDS)
        sample = evidence.observe(
            self.support_contacts(),
            com_world_m=(0.0, 0.12, 0.0),
            foot_positions_world_m={
                "left": (-0.03, 0.009, -0.008),
                "right": (0.03, 0.009, -0.008),
            },
        )
        sample["foot_positions_world_m"]["left"][0] = 99.0
        first_summary = evidence.summary()
        first_summary["last_sample"]["support_polygon_xz_m"].clear()

        second_summary = evidence.summary()
        self.assertEqual(-0.03, second_summary["last_sample"]
                         ["foot_positions_world_m"]["left"][0])
        self.assertEqual(4, len(second_summary["last_sample"]["support_polygon_xz_m"]))

    def test_rejects_nonfinite_or_incomplete_support_observations(self):
        valid_poses = {
            "left": (-0.03, 0.009, -0.008),
            "right": (0.03, 0.009, -0.008),
        }
        invalid_cases = (
            ((math.nan, 0.12, 0.0), valid_poses),
            ((0.0, 0.12), valid_poses),
            ((0.0, 0.12, 0.0), {"left": valid_poses["left"]}),
            (
                (0.0, 0.12, 0.0),
                {"left": valid_poses["left"], "right": (0.03, math.inf, 0.0)},
            ),
        )
        for com, poses in invalid_cases:
            with self.subTest(com=com, poses=poses), self.assertRaises(ValueError):
                ContactEvidence(self.FOOT_IDS).observe(
                    self.support_contacts(),
                    com_world_m=com,
                    foot_positions_world_m=poses,
                )


if __name__ == "__main__":
    unittest.main()
