import argparse
import json
import logging
from data.scanner import run_scan
from config import MIN_LIQUIDITY_USD, MAX_SPREAD_PCT, SCAN_LIMIT, MIN_VOLUME_24H
from pathlib import Path

def main() -> None:
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Desktop Tutorial Scanner")
    parser.add_argument("command", nargs="?", default="scan", choices=["scan", "status"], help="Command to execute")
    parser.add_argument("--min-liquidity", type=float, default=MIN_LIQUIDITY_USD, help="Minimum liquidity in USD")
    parser.add_argument("--max-spread", type=float, default=MAX_SPREAD_PCT, help="Maximum spread in percentage")
    parser.add_argument("--min-volume", type=float, default=MIN_VOLUME_24H, help="Minimum volume in 24 hours")
    parser.add_argument("--limit", type=int, default=SCAN_LIMIT, help="Limit of markets to scan")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--top", type=int, default=20, help="Number of top markets to display")
    args = parser.parse_args()

    if args.command == "status":
        if args.json:
            status = {
                "status": "ready",
                "config": {
                    "min_liquidity": MIN_LIQUIDITY_USD,
                    "max_spread": MAX_SPREAD_PCT,
                    "scan_limit": SCAN_LIMIT
                }
            }
            print(json.dumps(status, indent=4))
        else:
            print("scanner ready")
        return

    try:
        markets = run_scan(min_liquidity=args.min_liquidity, max_spread=args.max_spread, min_volume=args.min_volume, limit=args.limit)
    except Exception as e:
        logging.error(f"Error during scan: {e}")
        Path("errors").mkdir(parents=True, exist_ok=True)
        with open("errors/scan_error.log", "w") as f:
            f.write(f"Error during scan: {e}")
        return

    if args.json:
        json_output = []
        for m in markets:
            json_output.append({
                "id": m.id,
                "question": m.question,
                "liquidity": m.liquidity,
                "spread": m.spread,
                "volume_24h": m.volume_24h
            })
        print(json.dumps(json_output, indent=4))
    else:
        print(f"Found {len(markets)} markets")
        for m in markets[:args.top]:
            print(f"Market: {m.question}")

if __name__ == "__main__":
    main()
