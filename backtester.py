import asyncio
from typing import List, Dict, Optional

from core.models import Market
from data.polymarket_client import PolymarketClient
from data.filters import passes_liquidity_gate, passes_spread_gate, passes_volume_gate
from risk_engine import calculate_expected_value, calculate_fractional_kelly, determine_position_size

class Backtester:
    """
    Офлайн-оценка стратегий на истории.

    Этот класс выполняет оффлайн-оценку стратегий на основе исторических данных.
    Он использует данные с Polymarket, фильтрует рынки по заданным критериям и
    симулирует арбитражные стратегии для выбранных рынков.
    """

    def __init__(self, client: PolymarketClient, min_liquidity: float, max_spread: float, min_volume: float):
        self.client = client
        self.min_liquidity = min_liquidity
        self.max_spread = max_spread
        self.min_volume = min_volume

    async def fetch_historical_data(self, limit: int = 50) -> List[Market]:
        """
        Получает исторические данные о рынках.

        :param limit: Максимальное количество рынков для получения.
        :return: Список объектов Market.
        """
        return await self.client.fetch_markets(limit=limit)

    async def filter_markets(self, markets: List[Market]) -> List[Market]:
        """
        Фильтрует рынки по заданным критериям.

        :param markets: Список объектов Market для фильтрации.
        :return: Отфильтрованный список объектов Market.
        """
        filtered_markets = []
        for market in markets:
            if passes_liquidity_gate(market, self.min_liquidity) and \
               passes_spread_gate(market, self.max_spread) and \
               passes_volume_gate(market, self.min_volume):
                filtered_markets.append(market)
        return filtered_markets

    async def simulate_arbitrage(self, market: Market, outcome_probabilities: Dict[str, float]) -> float:
        """
        Симулирует арбитражные стратегии для выбранного рынка.

        :param market: Объект Market для симуляции.
        :param outcome_probabilities: Вероятности исходов для симуляции.
        :return: Ожидаемое значение, коэффициент Франка-Келли и размер позиции.
        """
        expected_value = calculate_expected_value(market, outcome_probabilities)
        fractional_kelly = calculate_fractional_kelly(market, outcome_probabilities)
        position_size = determine_position_size(market, outcome_probabilities, initial_capital=10000)
        return expected_value, fractional_kelly, position_size

    async def backtest_strategies(self, limit: int = 50) -> List[Dict]:
        """
        Выполняет оффлайн-оценку стратегий на основе исторических данных.

        :param limit: Максимальное количество рынков для оценки.
        :return: Список результатов оценки стратегий.
        """
        markets = await self.fetch_historical_data(limit)
        filtered_markets = await self.filter_markets(markets)
        results = []
        for market in filtered_markets:
            outcome_probabilities = {
                'outcome1': 0.6,
                'outcome2': 0.4  # Пример вероятностей исходов
            }
            result = await self.simulate_arbitrage(market, outcome_probabilities)
            results.append({
                'market_id': market.id,
                'expected_value': result[0],
                'fractional_kelly': result[1],
                'position_size': result[2]
            })
        return results

async def main():
    client = PolymarketClient()
    backtester = Backtester(client, min_liquidity=100000, max_spread=0.01, min_volume=100000)
    results = await backtester.backtest_strategies()
    print(results)

if __name__ == '__main__':
    asyncio.run(main())
