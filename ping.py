"""CLI-скрипт для замера скорости интернета через последовательные HTTP GET.

Подробности см. в README.md и в openspec/changes/add-internet-speed-ping/.
"""

import argparse
import asyncio
import json
import sys
import time
from argparse import ArgumentTypeError
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True, slots=True)
class SingleRequestResult:
    """Результат одного успешного HTTP GET: размер тела и время получения."""

    bytes: int
    duration_s: float


_MIB = 1024 * 1024


@dataclass(frozen=True)
class SpeedReport:
    """Итог по N последовательным замерам: успешные результаты + счётчик ошибок."""

    url: str
    results: list[SingleRequestResult] = field(default_factory=list)
    failed_count: int = 0

    def total_bytes(self) -> int:
        return sum(r.bytes for r in self.results)

    def total_time_s(self) -> float:
        return sum(r.duration_s for r in self.results)

    def aggregate_mbps(self) -> float:
        total_t = self.total_time_s()
        if total_t <= 0:
            return 0.0
        return self.total_bytes() / total_t / _MIB

    def per_request_mbps(self) -> list[float]:
        out: list[float] = []
        for r in self.results:
            if r.duration_s <= 0:
                continue
            out.append(r.bytes / r.duration_s / _MIB)
        return out


def validate_url(url: str) -> str:
    """Валидация URL для CLI: только http/https, непустой netloc."""
    if not url:
        raise ArgumentTypeError("URL не может быть пустым")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ArgumentTypeError(
            f"URL должен использовать схему http или https, получено: {parsed.scheme!r}"
        )
    if not parsed.netloc:
        raise ArgumentTypeError(f"URL должен содержать хост, получено: {url!r}")
    return url


async def measure_single(
    client: httpx.AsyncClient, url: str, timeout: float
) -> SingleRequestResult:
    """Один HTTP GET с замером времени от старта до получения всего тела.

    Бросает исключение на любой сетевой ошибке (connect, read, timeout, status>=400).
    """
    started = time.perf_counter()
    response = await client.get(url, timeout=timeout)
    await response.aread()
    duration = time.perf_counter() - started
    response.raise_for_status()
    return SingleRequestResult(bytes=len(response.content), duration_s=duration)


async def run_measurement(url: str, count: int, timeout: float) -> SpeedReport:
    """Сделать `count` последовательных запросов, собрать SpeedReport.

    Упавший запрос не абортит цикл — записывается в failed_count, идём дальше.
    Прогресс печатается в stderr, чтобы stdout оставался чистым для JSON-вывода.
    """
    report = SpeedReport(url=url)
    async with httpx.AsyncClient(http2=False) as client:
        for i in range(1, count + 1):
            try:
                result = await measure_single(client, url, timeout)
            except Exception as exc:  # noqa: BLE001 — намеренно глотаем ради partial failure
                print(
                    f"  [{i}/{count}] FAILED: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                report = SpeedReport(
                    url=report.url,
                    results=report.results,
                    failed_count=report.failed_count + 1,
                )
                continue
            print(
                f"  [{i}/{count}] {result.bytes} bytes in {result.duration_s:.2f}s",
                file=sys.stderr,
            )
            report = SpeedReport(
                url=report.url,
                results=report.results + [result],
                failed_count=report.failed_count,
            )
    return report


def _fmt_mib(size_bytes: int) -> str:
    return f"{size_bytes / _MIB:.2f}"


def _fmt_mbps(mbps: float) -> str:
    return f"{mbps:.2f}"


def print_report(report: SpeedReport) -> str:
    """Human-readable отчёт: per-request + aggregate + статистика."""
    lines: list[str] = []
    lines.append(f"URL: {report.url}")
    succeeded = len(report.results)
    failed = report.failed_count
    total = succeeded + failed
    lines.append(f"Sample: {succeeded} succeeded, {failed} failed (of {total})")

    if succeeded:
        total_b = report.total_bytes()
        total_t = report.total_time_s()
        agg = report.aggregate_mbps()
        lines.append("")
        lines.append("Per-request:")
        for i, r in enumerate(report.results, start=1):
            mbps = r.bytes / r.duration_s / _MIB if r.duration_s > 0 else 0.0
            lines.append(
                f"  [{i}/{total}] {_fmt_mib(r.bytes)} МБ / "
                f"{r.duration_s:.2f} с = {_fmt_mbps(mbps)} МБ/с"
            )

        lines.append("")
        lines.append(f"Итого: {_fmt_mib(total_b)} МБ за {total_t:.2f} с = {_fmt_mbps(agg)} МБ/с")

        per = report.per_request_mbps()
        if per:
            lines.append(
                f"Per-request Mbps: min={_fmt_mbps(min(per))}, "
                f"max={_fmt_mbps(max(per))}, mean={_fmt_mbps(sum(per) / len(per))}"
            )

    if failed:
        lines.append("")
        lines.append(f"Не удалось выполнить {failed} из {total} запросов.")

    lines.append("")
    return "\n".join(lines)


def to_json(report: SpeedReport) -> str:
    """Машиночитаемый JSON-отчёт."""
    payload = {
        "url": report.url,
        "count": len(report.results) + report.failed_count,
        "succeeded": len(report.results),
        "failed": report.failed_count,
        "total_bytes": report.total_bytes(),
        "total_time_s": report.total_time_s(),
        "aggregate_mbps": report.aggregate_mbps(),
        "per_request_mbps": report.per_request_mbps(),
    }
    return json.dumps(payload)


def main() -> int:
    """CLI entrypoint. Возвращает exit code (0/1/2)."""
    parser = argparse.ArgumentParser(
        prog="ping.py",
        description="Замер скорости интернета через последовательные HTTP GET.",
    )
    parser.add_argument(
        "--url",
        required=True,
        type=validate_url,
        help="URL картинки/файла для замера (http/https).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Количество последовательных запросов (по умолчанию 10).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Таймаут одного запроса в секундах (по умолчанию 10).",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Вывести отчёт в JSON-формате (для jq / парсинга).",
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        # argparse сам печатает usage в stderr и зовёт sys.exit(2)
        return 2

    if args.count < 1:
        print("--count должен быть >= 1", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("--timeout должен быть > 0", file=sys.stderr)
        return 2

    try:
        report = asyncio.run(run_measurement(args.url, args.count, args.timeout))
    except KeyboardInterrupt:
        print("\nПрервано пользователем", file=sys.stderr)
        return 1

    if args.as_json:
        print(to_json(report))
    else:
        print(print_report(report))

    return 1 if report.failed_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
