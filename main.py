import argparse
import json
from data.scanner import run_scan
from config import MIN_LIQUIDITY_USD, MAX_SPREAD_PCT, SCAN_LIMIT

def main() -> None:
    parser = argparse.ArgumentParser(description="Desktop Tutorial Scanner")
    parser.add_argument("command", nargs="?", default="scan", choices=["scan", "status"], help="Command to execute")
    parser.add_argument("--min-liquidity", type=float, default=MIN_LIQUIDITY_USD, help="Minimum liquidity in USD")
    parser.add_argument("--max-spread", type=float, default=MAX_SPREAD_PCT, help="Maximum spread in percentage")
    parser.add_argument("--limit", type=int, default=SCAN_LIMIT, help="Limit of markets to scan")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    if args.command == "status":
        print("scanner ready")
        return

    markets = run_scan(min_liquidity=args.min_liquidity, max_spread=args.max_spread, limit=args.limit)

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
        for m in markets[:20]:
            print(f"Market: {m.question}")

if __name__ == "__main__":
    main()
