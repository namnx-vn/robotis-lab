import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "simulation" / "webots" / "worlds" / "rl_h25_lab.wbt"


class WorldTests(unittest.TestCase):
    def test_world_declares_standard_gravity(self):
        self.assertRegex(WORLD.read_text(), r"(?m)^\s*gravity\s+9\.81\s*$")


if __name__ == "__main__":
    unittest.main()
