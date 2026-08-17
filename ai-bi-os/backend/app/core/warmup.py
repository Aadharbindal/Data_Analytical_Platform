"""Pay the cost of heavy imports at boot instead of on someone's first click.

statsmodels and scikit-learn are imported inside the functions that need them,
which keeps boot fast but hands the entire cost to whoever arrives first. That
is not free: importing statsmodels' Holt-Winters measured ~4.5s and
sklearn.linear_model ~16s on a cold process, and compute_kpis reaches
statsmodels through forecast_series - so the first dashboard load after every
restart paid for it. On a host that stops the service when idle, "after every
restart" means most first visits of the day.

Nothing here changes behaviour. It only moves when the import happens: into a
background thread at startup, while the deploy is still settling and nobody is
waiting. Later `import` statements then find the module already in sys.modules
and return immediately.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

# Only modules that a *user-facing* request would otherwise import mid-request.
# Ordered by how early a visitor is likely to hit them: the dashboard's KPI
# forecast comes first, the analytics pages after.
_MODULES = (
    "scipy.stats",
    "statsmodels.tsa.holtwinters",
    "sklearn.linear_model",
    "sklearn.preprocessing",
    "sklearn.model_selection",
    "sklearn.cluster",
    "sklearn.metrics",
)

_done = threading.Event()


def _load() -> None:
    import importlib

    started = time.perf_counter()
    for name in _MODULES:
        try:
            t = time.perf_counter()
            importlib.import_module(name)
            logger.info("Warmed %s in %.0fms", name, (time.perf_counter() - t) * 1000)
        except Exception as exc:
            # A missing optional dependency must not stop the server from
            # booting - the lazy import at the call site will fail the same way
            # it always would have, and only for the request that needs it.
            logger.warning("Could not warm %s: %s", name, exc)
    logger.info("Warmup finished in %.1fs", time.perf_counter() - started)
    _done.set()


def start_warmup() -> threading.Thread:
    """Begin loading in the background. Returns immediately.

    A daemon thread, so a shutdown during warmup is not held up by it.
    """
    thread = threading.Thread(target=_load, name="warmup", daemon=True)
    thread.start()
    return thread


def is_warm() -> bool:
    return _done.is_set()
