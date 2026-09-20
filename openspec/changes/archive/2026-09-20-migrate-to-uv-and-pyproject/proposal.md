# Proposal: migrate-to-uv-and-pyproject

## Why

Проект сейчас устанавливает зависимости через `pip install -r requirements.txt` с зафиксированными версиями прямыми зависимостями (httpx, pytest). Это рабочее решение, но не использует преимущества современного инструментария: `uv` устанавливает пакеты в 10-100x быстрее pip, автоматически создаёт и обновляет lock-файл (`uv.lock`) для воспроизводимых сборок, и нативно работает с `pyproject.toml` — современным стандартом декларации Python-проектов (PEP 621). Миграция — замена инструментария установки без изменения поведения скрипта.

## What Changes

- Добавляется `pyproject.toml` с секцией `[project]` (имя, версия, описание, `requires-python=">=3.10"`, `dependencies=["httpx>=0.28"]`) и `[project.optional-dependencies]` (dev = pytest).
- Добавляется `[build-system]` с `hatchling` для совместимости с `pip install -e .` и editable install (на будущее).
- Генерируется `uv.lock` через `uv lock` — фиксирует точные версии всех зависимостей (прямых и транзитивных) для воспроизводимых установок.
- **BREAKING для текущего workflow:** файл `requirements.txt` удаляется. Команда `pip install -r requirements.txt` перестаёт работать. Замена — `uv sync` (production) или `uv sync --extra dev` (с pytest).
- Обновляется секция `## Usage` в `README.md`: вместо инструкции `pip install httpx` — инструкция по `uv sync` / `uv run`.
- Существующий `.venv/` остаётся (uv использует его или создаёт свой — на выбор пользователя).
- `ping.py`, `tests/`, `openspec/specs/cli-ping/spec.md` — **не меняются**. Поведение скрипта, формат отчёта, exit codes — всё идентично.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет.

> **Skip specs:** это инфраструктурный change (замена инструментария сборки), поведение проекта не меняется. В `openspec/changes/migrate-to-uv-and-pyproject/.openspec.yaml` будет выставлен `skip_specs: true`. Существующая durable capability `cli-ping` остаётся без изменений — все её 7 требований (CLI interface, sequential measurement, per-request measurement, partial failure handling, human-readable report, machine-readable report, exit codes) выполняются тем же `ping.py`.

## Impact

- Новые файлы: `pyproject.toml`, `uv.lock`.
- Удаляемый файл: `requirements.txt`.
- Изменения: `README.md` (секция Usage обновляется).
- Без изменений: `ping.py`, `tests/`, `openspec/specs/cli-ping/spec.md`, `.gitignore`.
- Внешний эффект: разработчики, клонирующие репо, должны установить `uv` (https://docs.astral.sh/uv/) — `pip` больше не работает для первоначальной установки зависимостей.
- Поведение пользователя скрипта: без изменений (`python ping.py --url ...` работает как раньше через `uv run python ping.py --url ...` или после активации venv).
