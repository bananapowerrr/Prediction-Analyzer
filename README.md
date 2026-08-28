# Prediction Analyzer

Сканер и фильтр рынков предсказаний [Polymarket](https://polymarket.com): получает рынки через Gamma API и отсеивает их по ликвидности, спреду и объёму за 24 часа.

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env   # при необходимости настройте параметры
```

```bash
python main.py scan                                   # сканировать и отфильтровать рынки
python main.py status                                 # проверить готовность
```

### MVP: реальный скан

Быстрый запуск сканирования через Gamma API (без ключей):

```bash
python main.py scan --limit 5 --json
```

Команда берёт до 5 рынков из Gamma API и выводит отфильтрованный результат в JSON.

Ключевые флаги команды `scan`:

| Флаг | Назначение |
|---|---|
| `--min-liquidity USD` | Минимальная ликвидность в USD |
| `--max-spread PCT` | Максимальный спред в процентах |
| `--min-volume USD` | Минимальный объём за 24 ч |
| `--limit N` | Лимит сканируемых рынков |
| `--top N` | Сколько лучших рынков показать |
| `--json` | Вывод в формате JSON |
| `--out PATH` | Сохранить результаты (`--json`) в JSON-файл |

## Конфигурация

`config.py` (pydantic-settings) читает [`.env`](.env.example) из корня проекта: `RPC_*`, `LIQUIDITY_*` (мин. ликвидность/объём), `SPREAD_*` (макс. спред), `CONN_*` (Gamma API, таймаут, лимит сканирования). Динамические настройки рантайма — `core/config.py` (ключ/значение, JSON).

## Структура

```
desktop-tutorial/
├── main.py                  # CLI-точка входа
├── config.py                # настройки (pydantic-settings)
├── risk_engine.py           # гейты риска и расчёт позиции
├── state_manager.py         # хранилище состояния (SQLite)
├── data/                    # получение и фильтрация рыночных данных
│   ├── scanner.py           # MarketScanner / PolymarketScanner, run_scan
│   ├── filters.py           # гейты ликвидности/спреда/объёма
│   └── polymarket_client.py # клиент Gamma API
├── core/                    # переиспользуемое ядро
│   ├── config.py            # Config (key/value, JSON)
│   ├── models.py            # Market, Order
│   └── utils.py             # утилиты (clamp и др.)
└── tests/                   # автономные тесты pytest
```

## Архитектура

```
data/ → filters → risk/signals → main
```

- `data/` — получение рыночных данных (клиент Gamma API, сканер);
- `filters` — гейты ликвидности, спреда и объёма;
- `risk/signals` — гейты риска и сигналы;
- `main` — CLI-точка входа, связывает все этапы.

## Тесты

```bash
pytest tests/ -q          # быстрый запуск всех тестов
```