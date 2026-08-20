"""
Ultra-low-resource auto-clicker execution engine.
Optimized for 0% idle CPU and minimal RAM footprint (<10MB).
Uses standard library only (ctypes, time, random, threading).
"""

import sys
import time
import random
import threading
from hardware_input import UltraLightHardwareInput


class AutoClicker:
    """
    Micro-footprint automation core.
    - Zero busy-waiting: uses OS thread sleeping synchronized with winmm 1ms timer
    - Fast mutex-free state reads
    - Direct scancode hardware triggers
    """

    def __init__(
        self,
        target='f',
        is_mouse=False,
        mode='rapid',  # 'rapid' | 'hold'
        delay=0.05,    # 50ms (20 CPS)
        humanize=True,
        jitter_amount=0.012,
        min_dwell=0.015,
        max_dwell=0.030
    ):
        self.target = str(target).lower().strip()
        self.is_mouse = bool(is_mouse)
        self.mode = mode
        self.delay = max(0.001, float(delay))
        self.humanize = bool(humanize)
        self.jitter_amount = float(jitter_amount)
        self.min_dwell = float(min_dwell)
        self.max_dwell = float(max_dwell)

        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._hw = UltraLightHardwareInput()

    def update_config(self, **kwargs):
        """Hot-updates configuration without thread restarts."""
        if 'target' in kwargs:
            self.target = str(kwargs['target']).lower().strip()
        if 'is_mouse' in kwargs:
            self.is_mouse = bool(kwargs['is_mouse'])
        if 'mode' in kwargs:
            self.mode = kwargs['mode']
        if 'delay' in kwargs:
            self.delay = max(0.001, float(kwargs['delay']))
        if 'humanize' in kwargs:
            self.humanize = bool(kwargs['humanize'])
        if 'jitter_amount' in kwargs:
            self.jitter_amount = float(kwargs['jitter_amount'])
        if 'min_dwell' in kwargs:
            self.min_dwell = float(kwargs['min_dwell'])
        if 'max_dwell' in kwargs:
            self.max_dwell = float(kwargs['max_dwell'])

    def toggle(self) -> bool:
        if self.is_running:
            self.stop()
        else:
            self.start()
        return self.is_running

    def start(self):
        if not self.is_running:
            self._stop_event.clear()
            self.is_running = True
            self._thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self.is_running:
            self.is_running = False
            self._stop_event.set()
            self._release_safe()

    def _release_safe(self):
        try:
            if self.is_mouse:
                self._hw.mouse_up(self.target)
            else:
                self._hw.key_up(self.target)
        except Exception:
            pass

    def _worker_loop(self):
        # 1. Continuous Hold Mode
        if self.mode == 'hold':
            if self.is_mouse:
                self._hw.mouse_down(self.target)
            else:
                self._hw.key_down(self.target)

            # Wait on stop_event (0% CPU, OS kernel suspends thread until set)
            self._stop_event.wait()
            self._release_safe()
            return

        # 2. Rapid Burst Mode
        while not self._stop_event.is_set():
            dwell = (
                random.uniform(self.min_dwell, self.max_dwell)
                if self.humanize
                else 0.015
            )

            # Fire hardware press
            self._hw.trigger_press(self.target, self.is_mouse, dwell)

            # Sleep interval calculation with human micro-jitter
            base_delay = self.delay
            if self.humanize and self.jitter_amount > 0:
                jitter = random.uniform(-self.jitter_amount, self.jitter_amount)
                sleep_time = max(0.002, base_delay + jitter)
            else:
                sleep_time = base_delay

            # Sleep without busy-wait
            time.sleep(sleep_time)
