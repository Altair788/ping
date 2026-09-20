# Tasks

## 1. Tooling

- [x] 1.1 Установить `uv` через `pip install uv` или `brew install uv`; верифицировать что `uv --version` печатает версию.
- [x] 1.2 Создать `pyproject.toml` в корне проекта с финальным содержимым (см. ниже); верифицировать что файл валиден как TOML (`uv lock` принимает его без ошибок). Содержимое:

  ```toml
  [project]
  name = "ping"
  version = "0.1.0"
  description = "CLI скрипт-замерятель скорости интернета через последовательные HTTP GET"
  requires-python = ">=3.10"
  dependencies = [
      "httpx>=0.28",
  ]

  [project.optional-dependencies]
  dev = [
      "pytest>=9.0",
  ]

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  ```

## 2. Lock and Sync

- [x] 2.1 Сгенерировать `uv.lock` через `uv lock`; верифицировать что файл создан и не пустой.
- [x] 2.2 Запустить `uv sync --extra dev`; верифицировать что `.venv/` создан (или обновлён) и в нём есть httpx + pytest.
- [x] 2.3 Убедиться что существующие тесты проходят через uv: `uv run pytest tests/ -v` показывает 14/14 зелёных; верифицировать по выводу pytest.

## 3. Smoke

- [x] 3.1 Запустить скрипт через uv: `uv run python ping.py --url https://speed.cloudflare.com/__down?bytes=5000000 --count 2 --timeout 30`; верифицировать что отчёт печатается, exit code = 0, aggregate МБ/с > 0.

## 4. Cleanup

- [x] 4.1 Удалить `requirements.txt` (`rm requirements.txt`); верифицировать что `ls requirements.txt` возвращает «No such file or directory».
- [x] 4.2 Обновить секцию `## Usage` в `README.md`: заменить упоминания `pip install httpx` на `uv sync` / `uv run` workflow. Конкретные изменения:
  - В блоке «Требуется Python 3.10+ и пакет `httpx` (ставится в `.venv`: `pip install httpx`)» заменить на «Требуется [uv](https://docs.astral.sh/uv/) (`pip install uv` или `brew install uv`). Затем: `uv sync --extra dev`».
  - В примерах команд оставить `python ping.py --url ...` (читателю должно быть всё равно — `uv run` или прямой запуск из активированного venv).
  - В конце секции Usage добавить подсекцию «Development» с командами: `uv run pytest tests/ -v` (тесты), `uv run python ping.py --url ...` (запуск через uv).
  - Верифицировать что `cat README.md` показывает обновлённую секцию в читаемом виде.

## 5. Verification

- [x] 5.1 Прогнать полный smoke: `uv run pytest tests/ -v` — все 14 тестов зелёные.
- [x] 5.2 Прогнать CLI smoke: `uv run python ping.py --url http://127.0.0.1:1/nope --count 2 --timeout 3` — exit code = 1, в отчёте `failed >= 1`.
- [x] 5.3 Прогнать JSON smoke: `uv run python ping.py --url https://httpbin.org/bytes/2048 --count 1 --timeout 15 --json` 2>/dev/null — stdout содержит валидный JSON, `failed == 0`.
- [x] 5.4 Проверить что `ping.py` НЕ изменился: `git diff ping.py` показывает пустой вывод (или коммит первого change уже содержит его).

## 6. Wrap up

- [x] 6.1 Сделать `git add pyproject.toml uv.lock README.md openspec/changes/migrate-to-uv-and-pyproject/` (и `-A` для удалённого requirements.txt) и коммит с сообщением вроде `chore: migrate to uv and pyproject.toml`; верифицировать что `git log --oneline -2` показывает два коммита: первый `add-internet-speed-ping` (или аналог), второй этот.
- [x] 6.2 Прогнать `git status`; верифицировать что нет untracked файлов и нет «Changes not staged».
