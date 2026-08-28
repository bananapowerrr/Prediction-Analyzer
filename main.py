import argparse
import json
import logging
from data.scanner import run_scan
from data.ranking import rank_markets
from config import MIN_LIQUIDITY_USD, MAX_SPREAD_PCT, SCAN_LIMIT, MIN_VOLUME_24H, APP_VERSION
from pathlib import Path
from persistence import save_markets_json
import sys
from typing import Optional, List, Dict, Any

def main() -> None:
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(levelname)s PA %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Prediction Analyzer — сканер рынков Polymarket")
    parser.add_argument("command", nargs="?", default="scan", choices=["scan", "rank", "status", "version"], help="Команда для выполнения")
    parser.add_argument("--min-liquidity", type=float, default=MIN_LIQUIDITY_USD, help="Минимальная ликвидность в USD")
    parser.add_argument("--max-spread", type=float, default=MAX_SPREAD_PCT, help="Максимальный спред в процентах")
    parser.add_argument("--min-volume", type=float, default=MIN_VOLUME_24H, help="Минимальный объем за 24 часа")
    parser.add_argument("--limit", type=int, default=SCAN_LIMIT, help="Ограничение количества сканируемых рынков")
    parser.add_argument("--json", action="store_true", help="Вывод результатов в формате JSON")
    parser.add_argument("--top", type=int, default=20, help="Количество верхних рынков для отображения")
    parser.add_argument("--out", type=Path, help="Путь для сохранения результатов в JSON файл")
    args = parser.parse_args()

    if args.command == "version":
        if APP_VERSION:
            print(APP_VERSION)
        else:
            print("0.1.0")
        return

    if args.command == "status":
        if args.json:
            status = {
                "status": "ready",
                "app": "prediction-analyzer",
                "config": {
                    "min_liquidity": MIN_LIQUIDITY_USD,
                    "max_spread": MAX_SPREAD_PCT,
                    "scan_limit": SCAN_LIMIT,
                    "min_volume": MIN_VOLUME_24H
                }
            }
            print(json.dumps(status, indent=4))
        else:
            print("Prediction Analyzer готов")
        return

    try:
        markets = run_scan(min_liquidity=args.min_liquidity, max_spread=args.max_spread, min_volume=args.min_volume, limit=args.limit)
    except Exception as e:
        logging.error(f"Ошибка сканирования: {e}")
        Path("errors").mkdir(parents=True, exist_ok=True)
        with open("errors/scan_error.log", "w", encoding="utf-8") as f:
            f.write(f"Ошибка сканирования: {e}")
        sys.exit(1)

    if args.command == "rank":
        try:
            markets = rank_markets(markets)
        except Exception as e:
            logging.error(f"Ошибка сортировки: {e}")
            Path("errors").mkdir(parents=True, exist_ok=True)
            with open("errors/rank_error.log", "w", encoding="utf-8") as f:
                f.write(f"Ошибка сортировки: {e}")
            sys.exit(1)

    if args.json:
        json_output: List[Dict[str, Any]] = []
        for m in markets:
            entry: Dict[str, Any] = {
                "id": m.id,
                "question": m.question,
                "liquidity": m.liquidity,
                "spread": m.spread,
                "volume_24h": m.volume_24h
            }
            if hasattr(m, "score") and m.score is not None:
                entry["score"] = m.score
            json_output.append(entry)
        print(json.dumps(json_output, indent=4))
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            save_markets_json(json_output, args.out)
    else:
        print(f"Найдено {len(markets)} рынков")
        print(f"{'ID':<10}{'Question':<60}{'Liquidity':<15}{'Spread':<10}{'Volume 24h':<15}")
        for m in markets[:args.top]:
            print(f"{m.id:<10}{m.question[:60]:<60}{m.liquidity:<15}{m.spread:<10}{m.volume_24h:<15}")

if __name__ == "__main__":
    main()
