"""Offline ABI regression. Not a substitute for the native physics probe."""
import ctypes
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation/webots/controllers/rl_h25_controller"))
from disturbance import ForceWithOffsetAPI, TorqueAPI


class FakeNode:
    _ref = ctypes.c_void_p(0x1234)


class RecordingSymbol:
    def __init__(self):
        self.argtypes = None
        self.restype = 12
        self.calls = []

    def __call__(self, node, force, offset, relative):
        self.calls.append((node.value, list(force), list(offset), relative))


class RecordingTorqueSymbol:
    def __init__(self):
        self.argtypes = None
        self.restype = 12
        self.calls = []

    def __call__(self, node, torque, relative):
        self.calls.append((node.value, list(torque), relative))


class Library:
    def __init__(self):
        self.wb_supervisor_node_add_force_with_offset = RecordingSymbol()
        self.wb_supervisor_node_add_torque = RecordingTorqueSymbol()

    def wb_supervisor_node_add_force(self, *args):
        raise AssertionError("wrong C symbol (Webots R2025a Python binding defect)")


class ForceABIRegressions(unittest.TestCase):
    def test_exact_four_argument_abi_and_world_force(self):
        lib = Library()
        adapter = ForceWithOffsetAPI(FakeNode(), library=lib)
        adapter.add([0, 0, -0.1], [0, .04, 0], False)
        fn = lib.wb_supervisor_node_add_force_with_offset
        self.assertEqual([ctypes.c_void_p, ctypes.POINTER(ctypes.c_double),
                          ctypes.POINTER(ctypes.c_double), ctypes.c_bool], fn.argtypes)
        self.assertIsNone(fn.restype)
        self.assertEqual([(0x1234, [0, 0, -.1], [0, .04, 0], False)], fn.calls)
        self.assertEqual("r2025a_ctypes_force_with_offset", adapter.mode)

    def test_all_directions_and_relative_flag(self):
        lib = Library()
        api = ForceWithOffsetAPI(FakeNode(), library=lib)
        for vec in ([.1, 0, 0], [-.1, 0, 0],
                    [0, 0, .1], [0, 0, -.1]):
            api.add(vec, [0, .04, 0], False)
        self.assertEqual(4, len(lib.wb_supervisor_node_add_force_with_offset.calls))
        self.assertTrue(all(c[3] is False for c in lib.wb_supervisor_node_add_force_with_offset.calls))

    def test_no_silent_fallback_when_symbol_or_pointer_missing(self):
        for node in [object(), type("NullNode", (), {"_ref": ctypes.c_void_p()})()]:
            with self.assertRaises(RuntimeError):
                ForceWithOffsetAPI(node, library=Library())
        with self.assertRaises(RuntimeError):
            ForceWithOffsetAPI(FakeNode(), library=object())

    def test_reject_invalid_vector(self):
        api = ForceWithOffsetAPI(FakeNode(), library=Library())
        for f, o in [([0, 0], [0, .04, 0]),
                     ([float("nan"), 0, 0], [0, .04, 0]),
                     ([0, 0, 1], [0, float("inf"), 0])]:
            with self.assertRaises(ValueError):
                api.add(f, o, False)


class TorqueABIRegressions(unittest.TestCase):
    def test_exact_three_argument_abi_and_world_torque(self):
        lib = Library()
        adapter = TorqueAPI(FakeNode(), library=lib)
        adapter.add([0.0, 0.0, -0.01], False)
        fn = lib.wb_supervisor_node_add_torque
        self.assertEqual(
            [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_bool],
            fn.argtypes,
        )
        self.assertIsNone(fn.restype)
        self.assertEqual([(0x1234, [0.0, 0.0, -0.01], False)], fn.calls)
        self.assertEqual("r2025a_ctypes_torque", adapter.mode)

    def test_all_pitch_roll_directions_are_world_relative(self):
        lib = Library()
        api = TorqueAPI(FakeNode(), library=lib)
        for vector in ([0.01, 0, 0], [-0.01, 0, 0],
                       [0, 0, 0.01], [0, 0, -0.01]):
            api.add(vector, False)
        calls = lib.wb_supervisor_node_add_torque.calls
        self.assertEqual(4, len(calls))
        self.assertTrue(all(call[2] is False for call in calls))

    def test_no_silent_fallback_when_symbol_or_pointer_missing(self):
        for node in [object(), type("NullNode", (), {"_ref": ctypes.c_void_p()})()]:
            with self.assertRaises(RuntimeError):
                TorqueAPI(node, library=Library())
        library = Library()
        del library.wb_supervisor_node_add_torque
        with self.assertRaises(RuntimeError):
            TorqueAPI(FakeNode(), library=library)

    def test_rejects_invalid_vector(self):
        api = TorqueAPI(FakeNode(), library=Library())
        for vector in ([0, 0], [float("nan"), 0, 0], [0, float("inf"), 0]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                api.add(vector, False)


if __name__ == "__main__":
    unittest.main()
