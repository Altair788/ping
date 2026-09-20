"""Unit-тесты для SpeedReport и агрегаций. Без сети, без моков."""

import sys
from pathlib import Path

# Делаем ping.py доступным для импорта при запуске pytest из корня.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ping import SingleRequestResult, SpeedReport  # noqa: E402


def _make_report(*pairs: tuple[int, float]) -> SpeedReport:
    return SpeedReport(
        url="https://example.com/file.bin",
        results=[SingleRequestResult(b, d) for b, d in pairs],
    )


# --- 8.2: базовые методы ---


def test_total_bytes_sums_results() -> None:
    rep = _make_report((1_048_576, 1.0), (2_097_152, 1.0))
    assert rep.total_bytes() == 3_145_728


def test_total_time_s_sums_results() -> None:
    rep = _make_report((1_048_576, 1.0), (2_097_152, 1.0))
    assert rep.total_time_s() == 2.0


def test_aggregate_mbps_total_over_total_time() -> None:
    # 3 МБ за 2 с = 1.5 МБ/с
    rep = _make_report((1_048_576, 1.0), (2_097_152, 1.0))
    assert rep.aggregate_mbps() == 1.5


def test_per_request_mbps_per_result() -> None:
    # 1 МБ за 1 с = 1 МБ/с, 2 МБ за 1 с = 2 МБ/с
    rep = _make_report((1_048_576, 1.0), (2_097_152, 1.0))
    assert rep.per_request_mbps() == [1.0, 2.0]


# --- 8.3: пустой results (все запросы упали) ---


def test_empty_results_total_bytes_zero() -> None:
    rep = SpeedReport(url="https://x", failed_count=3)
    assert rep.total_bytes() == 0


def test_empty_results_total_time_zero() -> None:
    rep = SpeedReport(url="https://x", failed_count=3)
    assert rep.total_time_s() == 0


def test_empty_results_aggregate_mbps_zero() -> None:
    rep = SpeedReport(url="https://x", failed_count=3)
    assert rep.aggregate_mbps() == 0.0


def test_empty_results_per_request_mbps_empty_list() -> None:
    rep = SpeedReport(url="https://x", failed_count=3)
    assert rep.per_request_mbps() == []
