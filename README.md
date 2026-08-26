# Прогнозный анализатор

Программа для анализа прогнозов машинного обучения

## Запуск

1. Установите зависимости: `pip install -r requirements.txt`
2. Запустите программу: `python main.py`

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

