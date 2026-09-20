# Design: add-ci-and-ruff

## Context

Проект — CLI скрипт `ping.py` (~230 строк), `tests/` с 14 unit-тестами,
`pyproject.toml` (httpx + pytest, Python 3.10+). Репо публичное на GitHub
(`Altair788/ping`). Никаких CI workflow, никаких линтеров сейчас нет. README
уже описывает `uv sync` + `pytest` как developer workflow. Локально на этой
машине ruff не установлен, но ставится через `pip install ruff` за секунды.

GitHub Actions — единственный CI провайдер который имеет смысл: репо уже на
GitHub, бесплатен для публичных репо, не требует отдельной интеграции.

Ruff — единственный линтер который стоит рассматривать: объединяет flake8 +
isort + pyupgrade + black в один бинарь (написан на Rust), в ~100× быстрее
flake8, имеет единый opinionated набор правил и zero-config старт. Альтернативы
(`flake8 + black + isort`) — три инструмента, двойная конфигурация, медленнее.

## Goals / Non-Goals

**Goals:**
- Добавить минимальный CI на GitHub Actions, который запускает ruff (lint +
  format check) и pytest на каждом push и PR.
- Добавить минимальную конфигурацию ruff в `pyproject.toml` — `target-version`,
  `line-length`, минимальный `select` правил (E, F, W, I, B, UP — стандартный
  набор, ловит самые частые ошибки).
- Сохранить существующее поведение `ping.py` и 14/14 тестов зелёными.
- Сохранить backward-compat developer workflow: `uv sync --extra dev` и
  `uv run pytest tests/ -v` работают как раньше, ruff не обязан быть
  установлен локально для запуска тестов.

**Non-Goals:**
- Не вводим pre-commit hooks (ты работаешь в workflow «готовлю + ты
  коммитишь», ещё один слой автоматизации — overkill).
- Не добавляем coverage отчёты и badge.
- Не вводим matrix по Python-версиям (3.10/3.11/3.12/3.13) — README обещает
  3.10+, проверка на 3.11 в CI достаточна для сигнала.
- Не вводим mypy/pyright (типы в `ping.py` уже есть через dataclass, объём
  кода мал, type-checker не добавит ценности пропорционально шуму).
- Не включаем `RUF` правила (более opinionated и могут выдавать false
  positives на нашем dataclass-based коде).
- Не ставим ruff в `[project.optional-dependencies]` как dev dep — он нужен
  только для CI, не для runtime/test. Если разработчик хочет локально — пусть
  ставит сам через `pip install ruff` или `uv tool install ruff`.

## Decisions

### D1. GitHub Actions, single job, ubuntu-latest, Python 3.11

Почему один job: проект маленький, время выполнения ~30-60 секунд, matrix
ничего не даст кроме стоимости runner-минут. Python 3.11 — компромисс между
«есть в большинстве окружений» и «новее чем минимум 3.10» (3.11 уже GA
больше 4 лет, поддерживается core devs).

Альтернативы:
- macOS runner — медленнее и дороже, не нужно (скрипт кроссплатформенный,
  httpx работает везде).
- Windows runner — добавляет ещё один ось, не нужно.
- Self-hosted runner — есть смысл только при большом объёме CI, у нас нет.

### D2. Ruff правила: `E F W I B UP`, line-length 100, target py310

`E F W` — базовые PEP 8 + pyflakes (синтаксис, undefined names).
`I` — isort (импорт ordering).
`B` — flake8-bugbear (распространённые баги).
`UP` — pyupgrade (автоматическая модернизация syntax на новые Python).
`line-length = 100` — комфортнее дефолтных 88, но строже 120. README уже
использует строки <100.

Альтернативы:
- Только `E F` (минимум) — слишком мягко, не ловит очевидные баги (`B`
  стоит почти бесплатно).
- Полный `select = ["ALL"]` — даст сотни предупреждений на любом существующем
  коде, потребует массовых `# noqa`. Overkill.

### D3. ruff install в CI через `pip install ruff`, не через `astral-sh/setup-uv`

CI у нас чисто на pip + python из `actions/setup-python`. uv в CI не нужен —
мы не эмулируем локальный dev workflow проверяющего, мы просто запускаем
тесты и линтер. `pip install ruff httpx pytest` — тривиально и явно.

Альтернативы:
- `astral-sh/setup-uv@v3` + `uv sync --extra dev` — сэкономит 5-10 секунд
  за счёт uv-кэша, но в нашем случае избыточно (CI холодный старт доминирует).
- Кэширование pip через `actions/setup-python` cache — добавляет 5 строк
  YAML, экономит 2-3 секунды. Skip для первого CI; если будет медленно —
  добавим.

### D4. Single workflow file `.github/workflows/ci.yml`, name `CI`

Single file потому что один job. Если потом захотим добавить отдельный
release workflow — будет отдельный файл, не конфликтует.

Альтернативы:
- `reusable-workflows/` подход — для моно-репо с несколькими проектами, не
  наш случай.

### D5. Триггеры: `push` и `pull_request` на любую ветку

Логика: на любом push хочется знать что не сломалось, на PR — то же самое
(проверяющий или сам автор перед merge).

Альтернативы:
- Только на `main`/`develop` — пропустит feature branches и PR из форков
  (плохо для ревью).
- Явный список веток `branches: [main, develop]` — слишком жёстко для
  текущего workflow где активная разработка идёт в `develop` через feature
  ветки.

## Risks / Trade-offs

- **Risk:** ruff может сразу найти 1-3 несоответствия стилю в существующем
  `ping.py`. → **Mitigation:** перед добавлением workflow файла в коммит
  прогоняем `ruff check . && ruff format --check .` локально; если нашёл —
  чиним до merge. Если ничего не нашёл — workflow готов.
- **Risk:** GitHub Actions для PR из форков требует approval от
  maintainer-а. → **Mitigation:** в нашем workflow push делает только
  Eduard, форков нет, не релевантно.
- **Risk:** CI badge в README выглядит красиво, но добавлять не стали
  (anti-overengineering по профилю). → **Mitigation:** если Eduard
  захочет — добавим отдельным change.
- **Trade-off:** ruff не покрывает type-check (mypy). Для 230 строк это
  сознательное упрощение. Если код вырастет — добавим отдельным change.

## Migration Plan

Один коммит, атомарный:
1. Добавить `.github/workflows/ci.yml` и секцию `[tool.ruff]` в
   `pyproject.toml`.
2. Прогнать `ruff check . && ruff format --check . && pytest tests/ -v`
   локально — должно быть зелёным.
3. Push в `develop`. GitHub Actions запустится автоматически на первом push.

Rollback: `git revert <commit>` — оба файла уходят одним коммитом, ничего
не сломается.

## Open Questions

Нет.
