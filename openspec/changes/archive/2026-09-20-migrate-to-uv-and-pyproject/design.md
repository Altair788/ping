# Design: migrate-to-uv-and-pyproject

## Context

Сейчас проект использует `requirements.txt` с двумя строками (`httpx==0.28.1`, `pytest==9.1.1`) для фиксации прямых зависимостей. README говорит разработчикам использовать `pip install httpx` для первоначальной установки. Существующий `.venv/` содержит все нужные пакеты (httpx + pytest + их транзитивные зависимости), тесты проходят.

`uv` на этой машине ещё не установлен. Его нужно поставить перед генерацией `uv.lock`. Документация: https://docs.astral.sh/uv/.

Мотивация — в `proposal.md` (см. Why).

## Goals / Non-Goals

**Goals:**
- Заменить `requirements.txt` на стандартный `pyproject.toml`.
- Сгенерировать `uv.lock` через `uv lock` для воспроизводимых установок.
- Обновить README так, чтобы новый разработчик мог развернуть проект через `uv sync` за один шаг.
- Сохранить существующее поведение `ping.py` без изменений.
- Сохранить существующие тесты `tests/` без изменений — все 14 тестов должны остаться зелёными.

**Non-Goals:**
- Не превращаем `ping.py` в устанавливаемый пакет с entry-point (`pyproject.toml` декларирует проект, но `ping.py` остаётся скриптом, не библиотекой).
- Не добавляем Makefile / invoke / pre-commit хуки / CI.
- Не вводим `ruff` / `pyright` / `mypy` / линтеры.
- Не переписываем README целиком — только секция Usage.
- Не удаляем существующий `.venv/` — `uv sync` сам решит, использовать его или создать `.venv` с нуля.

## Decisions

### D1. Build backend: hatchling

**Решение:** `[build-system] requires=["hatchling"]`, `build-backend="hatchling.build"`.

**Почему:**
- Hatchling — современный стандарт, рекомендованный PyPA для новых проектов (https://packaging.python.org/en/latest/tutorials/packaging-projects/).
- Не требует конфигурации — `hatchling` сам находит `ping.py` в корне.
- Альтернативы (`setuptools`) — устаревший, плохо поддерживается; `poetry-core` — тащит экосистему poetry, overkill.

**Альтернативы:**
- Без `[build-system]` — uv будет работать, но `pip install -e .` сломается, и в экосистеме Python такой `pyproject.toml` считается неполным.
- `setuptools` — работает, но не рекомендован для новых проектов.

### D2. Зависимости: pinned minimum (`httpx>=0.28`), not exact (`==`)

**Решение:** `dependencies = ["httpx>=0.28"]`, `dev = ["pytest>=9.0"]`.

**Почему:**
- `>=` позволяет uv подтянуть минорные и патчевые обновления (security fixes).
- `uv.lock` фиксирует **точные** версии — это двойной уровень защиты: `pyproject.toml` говорит «хочу httpx», `uv.lock` говорит «используй именно 0.28.1».
- `==` в `pyproject.toml` — антипаттерн: блокирует обновления даже когда они безопасны.

**Альтернативы:**
- `==` — точные версии в `pyproject.toml`, lock-файл избыточен (но uv всё равно создаёт для скорости).
- `~=` (compatible release) — `httpx~=0.28` означает `>=0.28, <0.29`. Тоже рабочий вариант, но `>=` плюс lock гибче.

### D3. `requires-python = ">=3.10"`

**Решение:** минимальная версия Python 3.10.

**Почему:**
- Реально используемые фичи: `dataclass(slots=True)`, `match/case` (не используем), `f-strings` (3.6+).
- 3.10 — самая широкая совместимая версия. macOS Sonoma идёт с 3.9 по умолчанию, Ubuntu 22.04 — с 3.10.
- 3.11 / 3.12 дают незначительный выигрыш (лучше error messages, faster CPython), но ограничивают adoption без технической причины.

### D4. dev-dependencies, не основные

**Решение:** `httpx` — в `dependencies` (нужен для работы `ping.py`), `pytest` — в `[project.optional-dependencies].dev` (нужен только для тестов).

**Почему:**
- Пользователь, который хочет **только запустить** скрипт (`uv run python ping.py --url ...`), не должен тянуть pytest.
- В CI/разработке — `uv sync --extra dev` добавляет pytest.
- Это разделение — стандарт Python-экосистемы.

### D5. `uv.lock` — коммитим

**Решение:** `uv.lock` добавляется в git.

**Почему:**
- `uv.lock` обеспечивает воспроизводимость: один и тот же commit = один и тот же набор пакетов на любой машине.
- uv при каждом `uv sync` читает lock и проверяет что установленное совпадает с зафиксированным.
- `uv.lock` — бинарно-читаемый, но git diff на нём работает (TOML-формат внутри).

**Альтернатива:** не коммитить lock — но тогда разработчики на разных машинах могут получить разные версии транзитивных зависимостей. Для проекта из одного человека это ОК, для команды — нет.

## Risks / Trade-offs

- **[uv не установлен]** → разработчик должен поставить его (`brew install uv` или `pip install uv`). **Mitigation:** README явно указывает первый шаг.
- **[Lock-файл конфликтует при merge]** → если две ветки обновили `uv.lock`, merge будет нетривиальным. **Mitigation:** это стандартный workflow для любого lock-файла (Cargo.lock, package-lock.json); `uv lock --merge` или просто пересоздать lock на свежем `pyproject.toml`.
- **[Старый `.venv/` не совместим с uv]** → uv может попытаться использовать существующий venv, но это его `.venv` или системный. **Mitigation:** uv создаёт свой `.venv` по умолчанию, существующий venv можно удалить: `rm -rf .venv && uv sync`.
- **[Удаление `requirements.txt` ломает тех, кто использует `pip install -r requirements.txt`]** → **Mitigation:** README обновлён, `uv sync` — единственный supported путь.
- **`hatchling` пустой без `src/` или `pyproject.toml` указания пакетов** → **Mitigation:** мы НЕ делаем `pip install -e .` — это просто декларация проекта, build backend нужен для совместимости.

## Migration Plan

Шаги (применяются в порядке, описанном в `tasks.md`):

1. Создать `pyproject.toml` с финальным содержимым (см. proposal → Design → Tasks).
2. Установить uv: `pip install uv` или `brew install uv`.
3. Сгенерировать lock: `uv lock`.
4. Проверить что `uv sync --extra dev` устанавливает всё корректно.
5. Запустить тесты через uv: `uv run pytest tests/ -v` — должно быть 14/14 зелёных.
6. Запустить скрипт через uv: `uv run python ping.py --url https://speed.cloudflare.com/__down?bytes=5000000 --count 2` — должно работать.
7. Удалить `requirements.txt`.
8. Обновить README (секция Usage).
9. Коммит одним commit со всеми изменениями + OpenSpec-артефактами этого change.

**Rollback:** если что-то пошло не так:
- `git revert <commit>` откатывает все изменения.
- `pip install -r requirements.txt.bak` (если сохранить копию) — fallback.
- На практике: миграция чисто аддитивная (новые файлы + удаление одного), риск минимален.

## Open Questions

Нет. Все технические развилки разрешены в proposal (см. «Не входит в этот change») и в этом design (D1-D5).
