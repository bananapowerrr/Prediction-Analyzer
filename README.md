# Prediction Analyzer

Сканер рынков [Polymarket](https://polymarket.com): фильтрация по ликвидности, спреду и объёму через Gamma API.

## Установка

```bash
pip install -r requirements.txt
```

## Команды

| Команда | Описание |
|---------|----------|
| `scan` | Сканировать и отфильтровать рынки (по умолчанию) |
| `rank` | Сканировать + ранжировать по скору |
| `status` | Проверить готовность и текущую конфигурацию |
| `version` | Версия приложения |

## Примеры

```bash
python main.py scan                          # скан с параметрами по умолчанию
python main.py rank --top 5                  # топ-5 рынков по скору
python main.py scan --json --limit 10        # 10 рынков, вывод JSON
python main.py status --json                 # статус в JSON
```

## Флаги

| Флаг | Назначение | По умолчанию |
|------|------------|--------------|
| `--min-liquidity USD` | Минимальная ликвидность | из `.env` |
| `--max-spread PCT` | Максимальный спред, % | из `.env` |
| `--min-volume USD` | Минимальный объём за 24 ч | из `.env` |
| `--limit N` | Сколько рынков сканировать | из `.env` |
| `--top N` | Показать N лучших | 20 |
| `--json` | Вывод в JSON | — |
| `--out PATH` | Сохранить JSON в файл | — |

## Конфиг

Переменные задаются в `.env` (см. `.env.example`).

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `MIN_LIQUIDITY_USD` | Минимальная ликвидность, USD | 1000 |
| `MAX_SPREAD_PCT` | Максимальный спред, % | 0.1 |
| `SCAN_LIMIT` | Сколько рынков сканировать | 50 |
| `MIN_VOLUME_24H` | Минимальный объём за 24 ч, USD | 0 |

### Polygon RPC

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `RPC_ENDPOINT` | Основной RPC-эндпоинт | `https://polygon-rpc.com` |
| `RPC_ENDPOINTS` | Список RPC через запятую | `https://rpc.ankr.com/polygon,https://polygon.llamarpc.com` |
| `RPC_CHAIN_ID` | Chain ID | 137 |
| `RPC_PRIVATE_KEY` | Приватный ключ | — |
| `RPC_COOLDOWN_SECONDS` | Пауза между повторными попытками | 60 |
| `RPC_MAX_RETRIES` | Максимум повторов | 3 |
| `RPC_TIMEOUT_SECONDS` | Таймаут запроса | 10 |
| `RPC_REQUEST_TIMEOUT` | Таймаут ожидания ответа | 30 |

### Base RPC

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `BASE_RPC_ENDPOINT` | Основной RPC-эндпоинт | `https://mainnet.base.org` |
| `BASE_RPC_ENDPOINTS` | Список RPC через запятую | `https://mainnet.base.org` |
| `BASE_RPC_CHAIN_ID` | Chain ID | 8453 |
| `BASE_RPC_PRIVATE_KEY` | Приватный ключ | — |
| `BASE_RPC_COOLDOWN_SECONDS` | Пауза между повторными попытками | 60 |
| `BASE_RPC_MAX_RETRIES` | Максимум повторов | 3 |
| `BASE_RPC_TIMEOUT_SECONDS` | Таймаут запроса | 10 |
| `BASE_RPC_REQUEST_TIMEOUT` | Таймаут ожидания ответа | 30 |

### Фильтры

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `LIQUIDITY_MIN_LIQUIDITY_USD` | Минимальная ликвидность, USD | 1000 |
| `LIQUIDITY_MIN_VOLUME_24H` | Минимальный объём за 24 ч, USD | 0 |
| `SPREAD_MAX_SPREAD_PCT` | Максимальный спред, % | 0.1 |

### Подключение

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `CONN_GAMMA_API_BASE` | Базовый URL Gamma API | `https://gamma-api.polymarket.com` |
| `CONN_HTTP_TIMEOUT` | HTTP-таймаут | 30 |
| `CONN_SCAN_LIMIT` | Лимит сканирования | 50 |

### Облачные LLM

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `CLOUD_GROQ_API_KEY` | API-ключ Groq | — |
| `CLOUD_GROQ_MODEL` | Модель Groq | `llama-3.3-70b-versatile` |
| `CLOUD_GEMINI_API_KEY` | API-ключ Gemini | — |
| `CLOUD_GEMINI_MODEL` | Модель Gemini | `gemini-2.0-flash` |
| `CLOUD_OPENROUTER_API_KEY` | API-ключ OpenRouter | — |
| `CLOUD_OPENROUTER_MODEL` | Модель OpenRouter | `meta-llama/llama-3.3-70b-versatile` |
| `CLOUD_TIMEOUT` | Таймаут запроса | 30 |
| `CLOUD_MAX_CONCURRENT` | Макс. одновременных запросов | 5 |

### Локальный LLM (Ollama)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `LOCAL_OLLAMA_BASE_URL` | URL Ollama | `http://localhost:11434` |
| `LOCAL_JUDGE_MODEL` | Модель для оценки | `qwen2.5-coder:7b` |
| `LOCAL_TIMEOUT` | Таймаут запроса | 120 |
| `LOCAL_TEMPERATURE` | Температура генерации | 0.3 |
