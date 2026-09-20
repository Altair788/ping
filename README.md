Скрипт, который замеряет скорость интернета с компьютера пользователя.

Принимает адрес, куда стучаться (какая-нибудь тяжелая картинка), запускает последовательно 10 запросов к этому адресу, дожидается ответа, вычисляет среднее время запроса, объем скачанных данных и печатает в консоли скорость мб/с.

## Usage

Требуется Python 3.10+ и менеджер пакетов [uv](https://docs.astral.sh/uv/). Самый надёжный способ — `pipx install uv` (кроссплатформенный, обходит PEP 668 на Homebrew Python). Альтернативы: [standalone installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) (`curl -LsSf https://astral.sh/uv/install.sh | sh`) или `brew install uv` на macOS.

### Установка зависимостей

```
uv sync --extra dev
```

Эта команда создаст `.venv/` (или обновит существующий), прочитает `pyproject.toml` и `uv.lock`, установит `httpx` и `pytest` со всеми транзитивными зависимостями.

### Без uv (быстрый путь)

Если не хочется ставить `uv`, всё работает через стандартный venv + pip:

```
python3 -m venv .venv
source .venv/bin/activate
pip install httpx pytest
python ping.py --url https://speed.cloudflare.com/__down?bytes=10000000
```

После `source .venv/bin/activate` все команды ниже (`uv run ...`) можно заменить на прямой вызов (`python ping.py ...`, `pytest tests/ -v`).

### Базовый замер

```
uv run python ping.py --url https://speed.cloudflare.com/__down?bytes=10000000
```

Скрипт сделает 10 последовательных GET к указанному URL, замерит время каждого запроса и выведет human-readable отчёт: per-request результаты, aggregate МБ/с (общий объём / общее время), и статистику min/max/mean по отдельным замерам.

### Кастомные параметры

```
uv run python ping.py --url URL --count 3 --timeout 30
```

- `--count N` — количество запросов (по умолчанию 10).
- `--timeout SEC` — таймаут одного запроса в секундах (по умолчанию 10).

### Машиночитаемый вывод (JSON)

```
uv run python ping.py --url URL --json
```

Stdout содержит единственный JSON-объект со полями `url`, `count`, `succeeded`, `failed`, `total_bytes`, `total_time_s`, `aggregate_mbps`, `per_request_mbps`. Удобно для парсинга другими программами.

### Exit codes

| Код | Значение |
|-----|----------|
| 0   | Все запросы успешны |
| 1   | Как минимум один запрос упал (таймаут, сетевая ошибка, 4xx/5xx). Остальные выполнены, отчёт напечатан |
| 2   | Ошибка входа: не указан `--url`, URL невалидный, или `--count`/`--timeout` вне диапазона. HTTP-запросы не выполнялись |

### Пример human-readable вывода

```
URL: https://speed.cloudflare.com/__down?bytes=10000000
Sample: 3 succeeded, 0 failed (of 3)

Per-request:
  [1/3] 9.54 МБ / 1.64 с = 5.82 МБ/с
  [2/3] 9.54 МБ / 2.06 с = 4.62 МБ/с
  [3/3] 9.54 МБ / 2.10 с = 4.55 МБ/с

Итого: 28.61 МБ за 5.80 с = 4.93 МБ/с
Per-request Mbps: min=4.55, max=5.82, mean=5.00
```

### Development

```
uv run pytest tests/ -v
```

Запускает все unit-тесты (14 штук на чистую логику `SpeedReport` и `validate_url`). Тесты на сетевую часть не написаны — это сознательное решение (моки на httpx не дают реальной гарантии, smoke-проверки на Cloudflare покрывают runtime).

После изменения зависимостей в `pyproject.toml` не забывай пересоздать lock-файл:

```
uv lock
```