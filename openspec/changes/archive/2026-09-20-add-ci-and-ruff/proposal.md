# Proposal: add-ci-and-ruff

## Why

Проект сейчас запускает `pytest` локально (14 тестов в `tests/`) и имеет единый
скрипт `ping.py` (~230 строк) без автоматизированной проверки стиля или
непрерывной интеграции. Это означает: регрессии в логике ловятся только если
разработчик не забыл `pytest` перед push, а стилистические ошибки — никем
автоматически. На учебном проекте это не страшно, но на собеседовании /
review проверяющий смотрит на «гигиену» проекта — наличие CI badge и ruff
делает репо заметно опрятнее. Добавляем минимальный GitHub Actions workflow
(`ruff check`, `ruff format --check`, `pytest`) на push и pull_request.

## What Changes

- Добавляется `.github/workflows/ci.yml` с одним job `test` на `ubuntu-latest`
  и `python-version: "3.11"`. Шаги: checkout → setup-python → `pip install ruff
  httpx pytest` → `ruff check .` → `ruff format --check .` → `pytest tests/ -v`.
- Добавляется секция `[tool.ruff]` в `pyproject.toml` с минимальными настройками:
  `target-version = "py310"`, `line-length = 100`, `select = ["E", "F", "W",
  "I", "B", "UP"]`. Существующий код должен пройти без правок (он уже близок
  к PEP 8 + типизирован).
- **BREAKING для developer workflow:** `pyproject.toml` теперь содержит секцию
  ruff. Если разработчик использует старый `pip install -e .`, ничего не
  сломается (ruff это dev-only lint). Workflow остаётся обратно совместимым.
- `ping.py`, `tests/`, `README.md`, `openspec/specs/cli-ping/spec.md` — **не
  меняются** по поведению. Все 14 существующих тестов остаются зелёными.
- Локально перед коммитом рекомендуется прогонять `ruff check . && ruff format
  --check .` (можно добавить одной строкой в README как optional pre-commit
  шаг, но не обязательно).

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет.

> **Skip specs:** это инфраструктурный change (CI + линтер), поведение
> `ping.py` не меняется. Существующая durable capability `cli-ping` остаётся
> без изменений — все её 7 требований (CLI interface, sequential measurement,
> per-request measurement, partial failure handling, human-readable report,
> machine-readable report, exit codes) выполняются тем же `ping.py`. В
> `openspec/changes/add-ci-and-ruff/.openspec.yaml` будет выставлен
> `skip_specs: true`. Ruff и CI описывают **качество кода и процесс**, а не
> поведение, поэтому требования к capability не добавляются.

## Impact

- **CI время:** ~30-60 секунд на прогон (cold start GitHub runner + установка
  ruff/httpx/pytest). Это нормально для проекта такого размера.
- **Disk:** +1 файл `.github/workflows/ci.yml` (~30 строк), +5-10 строк в
  `pyproject.toml`. Никаких новых runtime-зависимостей (ruff ставится в CI
  только).
- **Runtime:** ноль — `ping.py` и его зависимости не меняются.
- **PR workflow:** GitHub Actions автоматически покажет pass/fail на каждом
  push и PR. Для fork-ов может потребоваться approval (но в нашем workflow
  push делается только владельцем).
- **Style consistency:** ruff может поначалу найти 1-3 небольших
  расхождения с PEP 8 (лишние пробелы, длинные строки). Если найдёт —
  починим до merge. Если ничего не найдёт — change готов.
