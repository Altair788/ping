# Tasks

## 1. Setup

- [ ] 1.1 Активировать существующий `.venv` и установить `httpx`; верифицировать что `python -c "import httpx; print(httpx.__version__)"` печатает версию без ошибок.
- [ ] 1.2 Создать файл `ping.py` в корне проекта с пустой `main()` и `if __name__ == "__main__": main()`; верифицировать что `python ping.py` запускается без ошибок.

## 2. Models

- [x] 2.1 Реализовать `@dataclass(frozen=True, slots=True) class SingleRequestResult(bytes: int, duration_s: float)`; верифицировать что конструктор принимает `(100, 0.5)`, попытка мутации (`r.bytes = 0`) бросает `FrozenInstanceError`, попытка добавить атрибут (`r.new = 1`) бросает `AttributeError` или `TypeError` (CPython `slots=True` бросает `TypeError` из C-слоя при попытке добавить необъявленный атрибут — это нормально и эквивалентно по смыслу «нельзя добавить атрибут»).
- [x] 2.2 Реализовать `@dataclass(frozen=True) class SpeedReport(url: str, results: list[SingleRequestResult], failed_count: int)` с методами `total_bytes`, `total_time_s`, `aggregate_mbps`, `per_request_mbps` (возвращает list[float] — по одному Mbps на каждый успешный результат, формула `bytes / duration_s / (1024*1024)`); верифицировать что на фикстуре из двух результатов `(1_048_576 байт, 1.0 с)` и `(2_097_152 байт, 1.0 с)` методы возвращают `total_bytes=3145728`, `total_time_s=2.0`, `aggregate_mbps=1.5` (3 МБ за 2 с), `per_request_mbps=[1.0, 2.0]`.

## 3. Validation

- [x] 3.1 Реализовать функцию `validate_url(url: str) -> str` через `urllib.parse.urlparse`: принимает только `http`/`https`, непустой `netloc`, возвращает нормализованный URL; бросает `argparse.ArgumentTypeError` с понятным сообщением на невалидный вход; верифицировать что `"https://example.com/x.bin"` возвращается как есть, `"ftp://x"` бросает `ArgumentTypeError`, `"not a url"` бросает `ArgumentTypeError`, `""` бросает `ArgumentTypeError`, `"https://"` бросает `ArgumentTypeError` (пустой netloc).

## 4. Measurement

- [x] 4.1 Реализовать `async def measure_single(client: httpx.AsyncClient, url: str, timeout: float) -> SingleRequestResult` с `time.perf_counter()` от старта до `await response.aread()`; на ошибке — бросает исключение с типом (не глотает); верифицировать что на локальном тестовом URL (см. 7.1) функция возвращает `SingleRequestResult` с положительными `bytes` и `duration_s`, а на заведомо битом URL (`http://127.0.0.1:1/nope`) бросает исключение за время ≤ `timeout`.
- [x] 4.2 Реализовать `async def run_measurement(url: str, count: int, timeout: float) -> SpeedReport` — создаёт `httpx.AsyncClient(http2=False)` в async with, последовательно вызывает `measure_single` в цикле, при исключении логирует и инкрементирует `failed_count` (НЕ бросает дальше, идёт к следующему запросу); верифицировать что на 3 запросах с `--count 3` (smoke test) возвращается `SpeedReport` с `len(results) + failed_count == 3`.

## 5. Reporting

- [x] 5.1 Реализовать `def print_report(report: SpeedReport) -> str` для human-readable вывода: заголовок с URL, пронумерованные per-request результаты (`[1/3] 1.2 МБ / 0.34 с = 3.5 МБ/с`), отдельная секция для failed с типом ошибки, итоговая строка `Итого: X МБ за Y с = Z МБ/с`, статистика `min/max/mean`; верифицировать что на фикстуре `SpeedReport` строка содержит ключевые числа (URL, total bytes, aggregate MB/s, min/max) и не содержит traceback.
- [x] 5.2 Реализовать `def to_json(report: SpeedReport) -> str` — JSON-объект с полями `url, count, succeeded, failed, total_bytes, total_time_s, aggregate_mbps, per_request_mbps`; верифицировать что `json.loads(to_json(report))` возвращает dict с ожидаемыми полями и типами.

## 6. CLI

- [x] 6.1 Реализовать `def main() -> int` с `argparse`: `--url` (required, type=validate_url), `--count` (default 10, type=int), `--timeout` (default 10.0, type=float), `--json` (action=store_true); вызывает `asyncio.run(run_measurement(...))`, печатает результат через `print_report` или `to_json`, возвращает exit code 0/1/2; верифицировать что `python ping.py` без аргументов печатает usage в stderr и возвращает exit code 2; `python ping.py --url ftp://x` печатает ошибку про схему и возвращает exit code 2; `python ping.py --url https://... --count 2` отрабатывает полный цикл (см. 7.1).

## 7. Verification

- [x] 7.1 Smoke test: запустить `python ping.py --url https://speed.cloudflare.com/__down?bytes=10000000 --count 3 --timeout 30` и верифицировать что скрипт печатает human-readable отчёт с 3 результатами, aggregate МБ/с > 0, exit code = 0.
- [x] 7.2 JSON smoke test: запустить `python ping.py --url https://speed.cloudflare.com/__down?bytes=10000000 --count 2 --timeout 30 --json` и верифицировать что stdout — валидный JSON с полями `url, count, succeeded, failed, total_bytes, total_time_s, aggregate_mbps, per_request_mbps`, `failed == 0`.
- [x] 7.3 Failure smoke test: запустить `python ping.py --url http://127.0.0.1:1/nope --count 2 --timeout 3` и верифицировать что в отчёте `failed >= 1`, exit code = 1.

## 8. Tests

- [x] 8.1 Установить `pytest` в `.venv`; верифицировать что `pytest --version` работает.
- [x] 8.2 Создать `tests/__init__.py` (пустой) и `tests/test_speed_report.py` с тестами на `SpeedReport.total_bytes`, `total_time_s`, `aggregate_mbps`, `per_request_mbps`; верифицировать что `pytest tests/test_speed_report.py` показывает все тесты зелёными.
- [x] 8.3 Добавить в `tests/test_speed_report.py` тесты для пустого `results` (все запросы упали): `total_bytes == 0`, `total_time_s == 0`, `aggregate_mbps == 0.0`, `per_request_mbps == []`; верифицировать что новые тесты зелёные.
- [x] 8.4 (опционально) Создать `tests/test_validation.py` с тестами на `validate_url` (валидный http/https, невалидные схемы, пустая строка, мусор); верифицировать что `pytest tests/test_validation.py` зелёный.

## 9. Documentation

- [x] 9.1 Добавить секцию `## Usage` в `README.md` с примерами: `python ping.py --url URL` (basic), `python ping.py --url URL --count 3 --timeout 30` (custom), `python ping.py --url URL --json` (machine-readable), таблицу exit codes; верифицировать что `cat README.md` показывает новую секцию в читаемом виде.

## 10. Wrap up

- [x] 10.1 Прогнать `pytest tests/` целиком и верифицировать что все тесты зелёные.
- [x] 10.2 Прогнать `ruff check ping.py tests/` и `ruff format --check ping.py tests/` (если ruff установлен); верифицировать что нет ошибок линтинга/форматирования. ruff в `.venv` отсутствует — пропускаем по условию задачи («если ruff установлен»); формат кода единообразный (4 пробела, type hints, f-strings), ручной review не выявил расхождений.
- [x] 10.3 Сделать `git add ping.py tests/ README.md openspec/changes/` и коммит с сообщением вроде `feat(ping): add internet speed ping CLI script`; верифицировать что `git log --oneline -1` показывает новый коммит на ветке `develop`.
