"""Tests for the startup warmup.

It exists because of a measurement: importing statsmodels' Holt-Winters cost
~4.5s and sklearn.linear_model ~16s on a cold process, and both were imported
inside the functions that use them. compute_kpis reaches statsmodels through
its forecast, so the first dashboard load after every restart paid for it -
and on a host that sleeps when idle, that is most first visits of the day.

What matters here is not that the imports are fast. It is that they happen off
the request path, and that a broken one cannot stop the server from starting.
"""

import sys
import threading

from app.core import warmup


def test_the_modules_are_actually_in_memory_afterwards():
    warmup._load()
    # The point of the exercise: a later `import` inside a request handler now
    # finds these already loaded and returns immediately.
    assert "scipy.stats" in sys.modules
    assert "statsmodels.tsa.holtwinters" in sys.modules


def test_a_missing_module_does_not_stop_the_rest(monkeypatch):
    tried = []

    def _fake_import(name):
        tried.append(name)
        if name == "sklearn.linear_model":
            raise ImportError("not installed here")

    monkeypatch.setattr(warmup, "_MODULES", ("scipy.stats", "sklearn.linear_model", "sklearn.metrics"))
    import importlib
    monkeypatch.setattr(importlib, "import_module", _fake_import)

    warmup._load()

    # An optional dependency that is absent must not cost the deploy its
    # remaining warmups - or, worse, the boot itself.
    assert tried == ["scipy.stats", "sklearn.linear_model", "sklearn.metrics"]


def test_starting_it_does_not_block_the_caller():
    started = threading.Event()
    warmup._done.clear()

    thread = warmup.start_warmup()
    started.set()

    # start_warmup returned while the work is still queued or running: startup
    # must not wait on several seconds of imports before it can serve /health.
    assert started.is_set()
    assert isinstance(thread, threading.Thread)
    assert thread.daemon  # a shutdown mid-warmup is not held up by it

    thread.join(timeout=120)
    assert warmup.is_warm()


def test_it_reports_when_it_has_finished():
    warmup._done.clear()
    assert warmup.is_warm() is False
    warmup._load()
    assert warmup.is_warm() is True
