# Tasks

## 1. Tooling

- [x] 1.1 Установить `ruff` локально (`pip install ruff` заблокирован PEP 668 на Homebrew Python — использован `pipx install ruff`) и верифицировать что `ruff --version` печатает версию (`ruff 0.16.8`).

## 2. Ruff baseline

- [x] 2.1 Прогнать `ruff check .` в корне проекта; верифицировать что вывод либо пустой, либо содержит только тривиальные fixable warnings. — найдено 3 fixable (F841 unused `exc`, RUF100 два unused `# noqa: E402`).
- [x] 2.2 Прогнать `ruff format --check .` в корне проекта; верифицировать что выводит `N files already formatted` (без списка файлов, которые нужно отформатировать). — `ping.py` имел 3 длинные строки.
- [x] 2.3 Если ruff нашёл что-то нетривиальное — починить стиль в `ping.py` и/или `tests/`, прогнать заново и убедиться что оба шага 2.1 и 2.2 чистые. — `ruff check --fix .` (3 fixed) + `ruff format .` (1 file reformatted). После: `ruff check .` → All checks passed; `ruff format --check .` → 16 files already formatted; `pytest tests/ -v` → 14/14 PASSED.

## 3. Конфигурация

- [x] 3.1 Добавить секцию `[tool.ruff]` в `pyproject.toml` со следующим содержимым:
  ```toml
  [tool.ruff]
  target-version = "py310"
  line-length = 100

  [tool.ruff.lint]
  select = ["E", "F", "W", "I", "B", "UP"]
  ```
  Верифицировать что `ruff check .` и `ruff format --check .` после этого всё ещё зелёные (конфиг не должен ломать существующий код). — После добавления конфига появилось E501 на одной строке (105 > 100); строка разбита вручную на два f-литерала, после чего `ruff check .` → All checks passed, `ruff format --check .` → 16 files already formatted, `pytest tests/ -v` → 14/14 PASSED.

## 4. CI workflow

- [x] 4.1 Создать `.github/workflows/ci.yml` со следующим содержимым:
  ```yaml
  name: CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: "3.11"
        - run: pip install ruff httpx pytest
        - run: ruff check .
        - run: ruff format --check .
        - run: pytest tests/ -v
  ```
  Верифицировать что файл создан, синтаксис YAML валиден (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` проходит). — YAML parsed через `uv run --with pyyaml python3`: top-level keys `['name', 'on', 'jobs']`, jobs → `test`, 6 steps, triggers `['push', 'pull_request']`.

## 5. Локальная верификация

- [x] 5.1 Прогнать `ruff check . && ruff format --check .` в корне проекта; верифицировать оба зелёные. — `All checks passed!` + `16 files already formatted`.
- [x] 5.2 Прогнать `uv run pytest tests/ -v` (или `python -m pytest tests/ -v`); верифицировать 14/14 тестов зелёные. — `14 passed in 0.05s`.

## 6. Wrap up

- [x] 6.1 Проверить `git status` и `git diff --stat`; убедиться что изменения только в `.github/workflows/ci.yml` и `pyproject.toml` (никаких случайных модификаций `ping.py`, `tests/`, `README.md`).
  - Modified: `ping.py` (ruff format + unused var), `pyproject.toml` (секция ruff), `tests/test_speed_report.py` + `tests/test_validation.py` (unused `# noqa: E402`).
  - Untracked: `.github/workflows/ci.yml` (новый CI workflow), `openspec/changes/add-ci-and-ruff/` (planning artifacts — заархивируются в шаге 6.3).
  - `README.md` НЕ тронут — как и обещано в design.
- [x] 6.2 Прогнать `openspec validate add-ci-and-ruff`; верифицировать что change валиден и нет ошибок. — `Change 'add-ci-and-ruff' is valid`.
- [x] 6.3 Заархивировать change: `openspec archive add-ci-and-ruff --yes`; верифицировать что `openspec/changes/add-ci-and-ruff/` переехал в `openspec/changes/archive/2026-09-20-add-ci-and-ruff/` без ошибок. — Archive done (`Change 'add-ci-and-ruff' archived as '2026-09-20-add-ci-and-ruff'`); warning про 1 incomplete task был про сам этот чекбокс (классический catch-22 — отмечаем после архивации).
