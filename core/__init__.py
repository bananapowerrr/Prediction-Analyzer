"""
Prediction Analyzer

Этот модуль содержит основные компоненты и функции для анализа предсказаний.

Модули:
- core.blockchain: Обработка блокчейн-операций.
- core.config: Конфигурация приложения.
- core.exceptions: Исключения приложения.
- core.logger: Настройка логирования.
- core.models: Модели данных.
- data.filters: Фильтры для данных.
- data.polymarket_client: Клиент API Polymarket.
- data.rpc_failover: Обработка отказоустойчивости RPC.
- execution.order_executor: Выполнение заказов.
- execution.state_machine: Машина состояний для заказов.
- execution.supervisor: Супервайзер для транзакций.
- market_connector: Подключение к рынкам.
- persistence: Постоянное хранение данных.
- quantitative_signals: Генерация квантовых сигналов.
- risk_engine: Риск-менеджмент.
- state_manager: Управление состоянием.
- telemetry: Телеметрия и отслеживание ошибок.

Опционально re-export Market из core.models:
- core.models.Market
"""

from .models import Market
