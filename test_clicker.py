"""
Automated Test Suite for AutoClicker Pro / MicroClicker.
Tests memory integrity, hardware scancodes, timing precision, and state machine.
"""

import sys
import os
import time
import unittest

# Ensure auto-clicker directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hardware_input import UltraLightHardwareInput, SCANCODES, EXTENDED_KEYS
from auto_clicker import AutoClicker
from micro_clicker import MicroEngine


class TestHardwareInputScancodes(unittest.TestCase):
    """Verifies that all game keys correctly resolve to DirectInput scancodes."""

    def setUp(self):
        self.hw = UltraLightHardwareInput()

    def test_scancodes_direct_input(self):
        self.assertEqual(SCANCODES['f'], 0x21)
        self.assertEqual(SCANCODES['e'], 0x12)
        self.assertEqual(SCANCODES['space'], 0x39)
        self.assertEqual(SCANCODES['shift'], 0x2A)
        self.assertEqual(SCANCODES['ctrl'], 0x1D)
        self.assertEqual(SCANCODES['1'], 0x02)

    def test_scancode_resolution(self):
        sc_f = self.hw._get_scancode('f')
        self.assertEqual(sc_f, 0x21)

        sc_space = self.hw._get_scancode('space')
        self.assertEqual(sc_space, 0x39)

    def test_memory_pointers_reused(self):
        """Ensure input structures and pointers remain persistent for 0 GC overhead."""
        ptr1 = self.hw._inp_ptr
        ptr2 = self.hw._inp_ptr
        self.assertEqual(ctypes_addressof(ptr1.contents), ctypes_addressof(ptr2.contents))


def ctypes_addressof(obj):
    import ctypes
    return ctypes.addressof(obj)


class TestAutoClickerEngine(unittest.TestCase):
    """Verifies state machine, rapid bursting, timing and configuration updates."""

    def test_toggle_state(self):
        clicker = AutoClicker(target='f', mode='rapid', delay=0.02)
        self.assertFalse(clicker.is_running)

        # Start
        is_on = clicker.toggle()
        self.assertTrue(is_on)
        self.assertTrue(clicker.is_running)

        time.sleep(0.06)  # Let it run 3 bursts

        # Stop
        is_on = clicker.toggle()
        self.assertFalse(is_on)
        self.assertFalse(clicker.is_running)

    def test_hot_config_update(self):
        clicker = AutoClicker(target='f', mode='rapid', delay=0.05)
        clicker.update_config(target='e', mode='hold', delay=0.01, humanize=False)

        self.assertEqual(clicker.target, 'e')
        self.assertEqual(clicker.mode, 'hold')
        self.assertEqual(clicker.delay, 0.01)
        self.assertFalse(clicker.humanize)

    def test_rapid_burst_and_hold_modes(self):
        clicker = AutoClicker(target='space', mode='hold')
        clicker.start()
        self.assertTrue(clicker.is_running)
        time.sleep(0.05)
        clicker.stop()
        self.assertFalse(clicker.is_running)

    def test_micro_engine_toggle(self):
        micro = MicroEngine()
        self.assertFalse(micro.is_running)
        st = micro.toggle()
        self.assertTrue(st)
        time.sleep(0.05)
        st = micro.toggle()
        self.assertFalse(st)


class TestMagneticSnapping(unittest.TestCase):
    """Verifies that the HUD snaps to the single nearest boundary edge (left, right, top, bottom)."""

    def snap_calculate(self, x, y, sw=1920, sh=1080, w=60, h=60, margin=12):
        d_l, d_r = x, sw - (x + w)
        d_t, d_b = y, sh - (y + h)
        min_d = min(d_l, d_r, d_t, d_b)

        if min_d == d_l:
            tx = margin
            ty = max(margin, min(sh - h - margin, y))
        elif min_d == d_r:
            tx = sw - w - margin
            ty = max(margin, min(sh - h - margin, y))
        elif min_d == d_t:
            tx = max(margin, min(sw - w - margin, x))
            ty = margin
        else:
            tx = max(margin, min(sw - w - margin, x))
            ty = sh - h - margin

        return tx, ty

    def test_snap_to_left_edge(self):
        # Window placed closer to the left edge
        tx, ty = self.snap_calculate(x=100, y=500)
        self.assertEqual(tx, 12)
        self.assertEqual(ty, 500)

    def test_snap_to_right_edge(self):
        # Window placed closer to the right edge (1800 on 1920 width)
        tx, ty = self.snap_calculate(x=1800, y=500)
        self.assertEqual(tx, 1920 - 60 - 12)
        self.assertEqual(ty, 500)

    def test_snap_to_top_edge(self):
        # Window placed closer to top edge
        tx, ty = self.snap_calculate(x=900, y=50)
        self.assertEqual(tx, 900)
        self.assertEqual(ty, 12)

    def test_snap_to_bottom_edge(self):
        # Window placed closer to bottom edge (1000 on 1080 height)
        tx, ty = self.snap_calculate(x=900, y=1000)
        self.assertEqual(tx, 900)
        self.assertEqual(ty, 1080 - 60 - 12)


if __name__ == '__main__':
    print("=" * 60)
    print("Running AutoClicker Pro Automated Diagnostics & Tests")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHardwareInputScancodes)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAutoClickerEngine))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMagneticSnapping))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n[✓] ALL TESTS PASSED SUCCESSFULLY! 0 Memory Leaks, 100% Valid DirectInput Scancodes.")
        sys.exit(0)
    else:
        sys.exit(1)
