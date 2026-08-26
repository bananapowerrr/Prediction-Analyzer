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

