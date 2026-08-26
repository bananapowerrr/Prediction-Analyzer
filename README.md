# Прогнозный анализатор

Программа для анализа прогнозов машинного обучения

## Запуск

1. Установите зависимости: `pip install -r requirements.txt`
2. Запустите программу: `python main.py`

## Тестирование и разработка

### Запуск тестов

Проект использует [pytest](https://docs.pytest.org/). Тесты находятся в каталоге `tests/`
и покрывают конфигурацию (`config.py`), движок рисков (`risk_engine.py`),
менеджер состояния (`state_manager.py`), сканер и фильтры рынков.

Запуск всех тестов из корня проекта:

```bash
python -m pytest
```

Запуск конкретного файла:

```bash
python -m pytest tests/test_core.py
```

Запуск одного теста по имени:

```bash
python -m pytest tests/test_core.py::test_settings_defaults
```

Полезные флаги:

- `-v` — подробный вывод по каждому тесту;
- `-x` — остановиться на первом упавшем тесте;
- `--lf` — перезапустить только упавшие в прошлый раз тесты;
- `-k "scanner"` — запустить тесты, чьи имена содержат `scanner`.

Тесты не требуют внешних сервисов и сетевого доступа: конфигурация
проверяется на значениях по умолчанию, а работа с состоянием — через
временные файлы (`tmp_path`).

### Управление конфигурацией

Конфигурация приложения описана в `config.py` с помощью
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
Все настройки группируются в классе `Settings`, состоящем из вложенных блоков:

| Блок | Префикс переменных | Назначение |
|------|--------------------|------------|
| `rpc` | `RPC_` | RPC-эндпоинт, chain id, приватный ключ |
| `liquidity_gate` | `LIQUIDITY_` | Мин. ликвидность и объём за 24ч |
| `spread` | `SPREAD_` | Макс. допустимый спред |
| `connection` | `CONN_` | Базовый URL Gamma API, таймаут, лимит сканирования |

#### Переменные окружения и `.env`

Настройки читаются из переменных окружения и/или файла `.env` в корне проекта
(кодировка UTF-8). Файл `.env` добавлен в `.gitignore` и не попадает в репозиторий.

Для локальной настройки скопируйте пример и отредактируйте значения:

```bash
cp .env.example .env
```

Пример содержимого `.env`:

```ini
MIN_LIQUIDITY_USD=1000
MAX_SPREAD_PCT=0.1
SCAN_LIMIT=50
MIN_VOLUME_24H=0

RPC_ENDPOINT=https://polygon-rpc.com
RPC_CHAIN_ID=137
RPC_PRIVATE_KEY=

LIQUIDITY_MIN_LIQUIDITY_USD=1000
LIQUIDITY_MIN_VOLUME_24H=0

SPREAD_MAX_SPREAD_PCT=0.1

CONN_GAMMA_API_BASE=https://gamma-api.polymarket.com
CONN_HTTP_TIMEOUT=30
CONN_SCAN_LIMIT=50
```

Переменные окружения имеют приоритет над значениями по умолчанию в коде.
Префикс (например `RPC_`) указывается перед именем поля (например `RPC_ENDPOINT`).

#### Значения по умолчанию

Если `.env` отсутствует или переменная не задана, используются значения,
определённые в `config.py`:

```python
from config import settings

print(settings.rpc.endpoint)            # https://polygon-rpc.com
print(settings.liquidity_gate.min_liquidity_usd)  # 1000.0
print(settings.connection.scan_limit)   # 50
```

Удобные константы верхнего уровня (`MIN_LIQUIDITY_USD`, `MAX_SPREAD_PCT`,
`SCAN_LIMIT`, `GAMMA_API_BASE`, `MIN_VOLUME_24H`, `HTTP_TIMEOUT`) импортируются
прямо из `config.py` и ссылаются на текущий экземпляр `settings`.

#### Конфигурация в рантайме (`core/config.py`)

Для динамических настроек внутри кода (не из `.env`) используется класс
`core.config.Config` — простое хранилище ключ/значение с загрузкой и
сохранением в JSON:

```python
from core.config import Config

cfg = Config(defaults={"threshold": 0.5})
cfg.set("threshold", 0.8)
cfg.get("threshold")            # 0.8
cfg.save("config/settings.json")
cfg.load("config/settings.json")
```

Методы: `get`, `set`, `update`, `as_dict`, `load` (из JSON, если файл существует),
`save` (создаёт каталоги при необходимости). Это независимый от `config.py`
механизм для пользовательских параметров выполнения.

## API

Программа предоставляет программный интерфейс для сканирования и фильтрации рынков предсказаний.

### `data.scanner.scan_markets(...)`

Удобная точка входа для получения отфильтрованных рынков.

```python
from data.scanner import scan_markets

markets = scan_markets(
    min_liquidity=1000.0,  # мин. ликвидность в USD
    max_spread=2.0,        # макс. спред в процентах
    min_volume=500.0,      # мин. объём за 24ч
    limit=50,              # лимит рынков
)
for m in markets:
    print(m.id, m.question, m.liquidity, m.spread, m.volume_24h)
```

### `data.scanner.MarketScanner` / `PolymarketScanner`

Базовый класс `MarketScanner` инкапсулирует логику получения и фильтрации данных.
Реализация `PolymarketScanner` работает поверх Polymarket Gamma API.

```python
from data.scanner import PolymarketScanner, ScanConfig

scanner = PolymarketScanner(scan_config=ScanConfig(min_liquidity=1000.0))
markets = scanner.scan()  # возвращает список объектов Market
```

Основные методы:
- `fetch_raw()` — получение сырых записей из источника данных;
- `parse(raw)` — преобразование сырых записей в модели `Market`;
- `filter_markets(markets)` — применение фильтров по ликвидности/спреду/объёму;
- `scan()` — полный цикл: получение → разбор → фильтрация.

### `data.scanner.filter_by_volume_threshold(markets, min_volume)`

Возвращает рынки, чей объём за 24 часа не меньше `min_volume`.

### Модель `core.models.Market`

Поля: `id`, `question`, `liquidity`, `spread`, `volume_24h`.

---

# Архитектура проекта

`desktop-tutorial` — это торговый терминал для рынков предсказаний (Polymarket)
с мониторингом через веб-интерфейс (Streamlit). Приложение разбито на слои:
ввод/вывод (`ui/`), бизнес-логика (`core/`, `data/`, `execution/`,
`notifications/`, `agents/`), хранение состояния (`state_manager.py`) и
автономные тесты (`tests/`).

```
desktop-tutorial/
├── main.py                  # Точка входа консольного приложения
├── config.py                # Настройки (pydantic-settings, верхнего уровня)
├── state_manager.py         # Хранилище World State на SQLite
├── risk_engine.py           # Гейты риска и расчёт размера позиции
├── market_connector.py      # Подключение к рыночным данным
├── persistence.py           # Сохранение/загрузка данных
├── telemetry.py             # Телеметрия выполнения
├── backtester.py            # Прогон стратегий на истории
├── agents/
│   └── tribunal.py          # LLM-дебаты (TRIBUNAL)
├── core/                    # Переиспользуемое ядро (без зависимостей от UI)
│   ├── config.py            # Класс Config (key/value, JSON)
│   ├── exceptions.py        # Иерархия исключений
│   ├── logger.py            # Централизованное логирование
│   ├── models.py            # Дата-классы Order, Market
│   └── utils.py             # Утилиты (clamp и др.)
├── data/                    # Получение и фильтрация рыночных данных
│   ├── scanner.py           # MarketScanner / PolymarketScanner
│   ├── filters.py           # Гейты ликвидности/спреда/объёма
│   └── polymarket_client.py # Клиент Gamma API
├── execution/               # Исполнение ордеров
│   ├── order_executor.py    # OrderExecutor (async, CLOB API)
│   ├── state_machine.py     # Конечный автомат ордера
│   └── supervisor.py        # Надзор за исполнением
├── notifications/
│   └── telegram_bot.py      # Уведомления в Telegram
├── ui/                      # Графический интерфейс (Streamlit)
│   ├── app.py               # Полноценный монитор терминала
│   ├── main_window.py       # Каркас главного окна
│   ├── theme.py             # Управление темами (light/dark)
│   └── widgets.py           # Переиспользуемые виджеты
└── tests/                   # Автономные тесты pytest
```

## Модуль `core/` — ядро приложения

`core/` содержит инфраструктурный код, не зависящий от внешних сервисов и UI.
Его можно импортировать и тестировать изолированно.

| Файл | Назначение |
|------|------------|
| `core/__init__.py` | Пустой инициализатор пакета. |
| `core/config.py` | Класс `Config` — простое хранилище `key/value` с `get`/`set`/`update`/`as_dict`/`load`/`save` (JSON, с созданием каталогов). Независим от `config.py` верхнего уровня; для пользовательских параметров выполнения. |
| `core/exceptions.py` | Иерархия ошибок: `TutorialError` (базовая) → `ConfigError`, `UIError`. Другие модули (например `execution`) определяют собственные исключения. |
| `core/logger.py` | `setup_logging()` настраивает root-логгер консольным и ротирующимся файловым (`RotatingFileHandler`) обработчиками. `get_logger()` лениво инициализирует конфигурацию, `reset()` очищает обработчики (для тестов). |
| `core/models.py` | Дата-классы `Order` (валидация `side`, `size`, `price`) и `Market` (`id`, `question`, `liquidity`, `spread`, `volume_24h`). Используются в `data/`, `execution/`. |
| `core/utils.py` | `clamp(value, lo, hi)` — ограничение значения диапазоном. |

Соглашение: модули получают логгер через `logging.getLogger(__name__)`,
а конфигурация логирования централизованно задаётся из `core.logger`.

## Модуль `ui/` — графический интерфейс

Интерфейс построен на **Streamlit** (`requirements.txt`: `streamlit>=1.62.0`).
Все модули `ui/` добавляют корень проекта в `sys.path`, чтобы импортировать
модули верхнего уровня и `core/`.

| Файл | Назначение |
|------|------------|
| `ui/app.py` | Готовый монитор терминала: 4 вкладки — **World State**, **Tribunal**, **Edge**, **Order Execution**. Читает события из `StateManager` (`world_state.db`), поддерживает авто-обновление, переключение темы и генерацию демо-данных. Точка входа UI: `streamlit run ui/app.py`. |
| `ui/main_window.py` | Каркас главного окна: боковая панель (`render_sidebar`) + основная область (`render_main_area`) с вкладками «Сводка»/«Логи». Интегрирует `ui.theme.theme_switcher`. |
| `ui/theme.py` | Управление темами `light`/`dark`: `load_theme()`, `save_theme()`, `apply_theme()` (инъекция CSS), `theme_switcher()` (виджет выбора в `st.sidebar`, персист в `.ui_theme.json`). |
| `ui/widgets.py` | Переиспользуемые компоненты: `styled_button()` (варианты `primary`/`secondary`/`danger`) и `status_bar()` (цветовая индикация `idle`/`running`/`success`/`warning`/`error`). |

Общие соглашения `ui/`:
- Тема хранится в `PROJECT_ROOT/.ui_theme.json` (в `.gitignore`).
- Путь к БД World State берётся из переменной `WORLD_STATE_DB` или по
  умолчанию `PROJECT_ROOT/world_state.db`.
- Деградация «тихо»: ошибки `toast`/`markdown` перехватываются, чтобы UI не
  падал при недоступности отдельных функций.

## Модуль `tests/` — автономные тесты

Тесты написаны на **pytest** и не требуют сети или внешних сервисов
(используют `tmp_path`, фейковые сессии, синтетические данные).

| Файл | Что покрывает |
|------|---------------|
| `tests/test_config.py` | `core.config.Config`: инициализация, `get`/`set`/`update`, сохранение/загрузка JSON (в т.ч. вложенные структуры, unicode, отсутствующий файл, невалидный JSON), создание каталогов. |
| `tests/test_core.py` | Верхнеуровневые `config.Settings` (блоки `Rpc`/`LiquidityGate`/`Spread`/`Connection`), `risk_engine` (гейты ликвидности/спреда, EV, fractional Kelly, размер позиции) и `state_manager.StateManager` (`save_event`/`get_events`). |
| `tests/test_logger.py` | Ротирующийся `RotatingFileHandler`: запись в файл, уровни логов, создание бэкапов при ротации, соблюдение `backup_count`, дописывание после ротации. |
| `tests/test_utils.py` | `core.utils.clamp` на граничных значениях, дробных числах, инвертированных/отрицательных границах. |
| `tests/test_scanner.py` | `data.filters.passes_liquidity_gate`/`passes_spread_gate` и `data.scanner.filter_by_volume_threshold` на модели `core.models.Market`. |
| `tests/test_order_executor.py` | `execution.order_executor.OrderExecutor`: валидация `Order`, построение payload, `submit_order`/`cancel_order` с фейковой async-сессией (успех, повторы при HTTP 429, исчерпание попыток, 4xx без повтора, валидационные ошибки). |

Соглашение по тестам: файлы импортируют целевые модули напрямую
(`from core.config import Config`, `from config import Settings` и т.д.),
pytest запускается из корня проекта, поэтому `sys.path` корректен.

---

# Схема CI/CD

Конвейер описан в `.github/workflows/ci.yml` (GitHub Actions).

| Параметр | Значение |
|----------|----------|
| Триггеры | `push` и `pull_request` на любую ветку |
| Runner | `ubuntu-latest` |
| Python | `3.11` (через `actions/setup-python@v5`) |
| Шаги | 1) `checkout@v4`; 2) установка Python; 3) установка зависимостей; 4) `py_compile`; 5) `pytest` |

Подробно по шагам:

1. **Checkout** — `actions/checkout@v4` клонирует репозиторий.
2. **Set up Python** — `actions/setup-python@v5` с `python-version: "3.11"`.
3. **Install dependencies** (shell `pwsh`):
   ```pwsh
   python -m pip install --upgrade pip
   pip install pytest
   if (Test-Path -Path requirements.txt) { pip install -r requirements.txt }
   ```
   Устанавливается `pytest` явно, затем зависимости из `requirements.txt`
   (если файл существует).
4. **Run py_compile** — компиляция ВСЕХ `.py`-файлов (кроме `__pycache__`)
   для проверки синтаксиса:
   ```pwsh
   python -m py_compile $(Get-ChildItem -Recursive -Filter *.py -Exclude __pycache__ | Resolve-Path -Relative)
   ```
5. **Run pytest** — `pytest -v` (shell `pwsh`) запускает весь набор тестов.

> Замечание: CI использует PowerShell (`shell: pwsh`), поэтому команды
> написаны под Windows-синтаксис (`Test-Path`, `Get-ChildItem`), хотя
> runner — Linux. Это работает благодаря PowerShell Core (pwsh), доступному
> на `ubuntu-latest`.

Локально для воспроизведения CI выполните те же шаги:

```bash
python -m pip install --upgrade pip
pip install pytest
pip install -r requirements.txt
python -m py_compile $(Get-ChildItem -Recurse -Filter *.py -Exclude __pycache__ | Resolve-Path -Relative)  # pwsh
pytest -v
```

---

# Инструкции для конвейера разработчика

## 1. Подготовка окружения

```bash
cd D:\Workspace\desktop-tutorial
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env                # при необходимости настройте значения
```

## 2. Базовый цикл разработки

```bash
# Запуск консольного приложения
python main.py

# Запуск веб-интерфейса (Streamlit)
streamlit run ui/app.py

# Только каркас главного окна
streamlit run ui/main_window.py
```

## 3. Тестирование

```bash
python -m pytest                    # все тесты
python -m pytest tests/test_core.py # конкретный файл
python -m pytest tests/test_core.py::test_settings_defaults  # один тест
pytest -v -x --lf -k "scanner"      # подробно, стоп на падении,
                                    # только упавшие, фильтр по имени
```

Тесты изолированы: сеть не требуется, состояние пишется во временные файлы
(`tmp_path`), async-вызовы мокаются фейковыми сессиями.

## 4. Проверка перед коммитом (локальный «CI»)

```bash
# Синтаксическая компиляция всех модулей (как в CI)
python -m py_compile (Get-ChildItem -Recurse -Filter *.py -Exclude __pycache__ | Resolve-Path -Relative)

# Полный прогон тестов
pytest -v
```

## 5. Правила и соглашения

- **Не коммитьте** `.env`, `world_state.db`, `logs/`, `.ui_theme.json`,
  `__pycache__/` (все в `.gitignore`). Секреты (RPC-ключи) передаются только
  через переменные окружения / `.env`.
- **Никаких shell/git-команд внутри Python-файлов.** Файлы содержат только
  валидный код; операции с репозиторием выполняются вне кода.
- Импорты UI-модулей всегда добавляют корень проекта в `sys.path` — не
  удаляйте этот блок.
- Логирование — только через `logging.getLogger(__name__)`; конфигурация
  централизована в `core.logger.setup_logging`.
- Новые доменные модели добавляйте в `core/models.py`; новые исключения —
  в `core/exceptions.py` (наследуйте от `TutorialError`).
- При добавлении функциональности кладите тесты в `tests/` рядом с целевым
  модулем и проверяйте, что они проходят без внешних зависимостей.

