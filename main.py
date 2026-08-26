import argparse
from data.scanner import run_scan
from config import MIN_LIQUIDITY_USD, MAX_SPREAD_PCT, SCAN_LIMIT

def main() -> None:
    parser = argparse.ArgumentParser(description="Desktop Tutorial Scanner")
    parser.add_argument("command", nargs="?", default="scan", choices=["scan", "status"], help="Command to execute")
    parser.add_argument("--min-liquidity", type=float, default=MIN_LIQUIDITY_USD, help="Minimum liquidity in USD")
    parser.add_argument("--max-spread", type=float, default=MAX_SPREAD_PCT, help="Maximum spread in percentage")
    parser.add_argument("--limit", type=int, default=SCAN_LIMIT, help="Limit of markets to scan")
    args = parser.parse_args()

    if args.command == "status":
        print("scanner ready")
        return

    markets = run_scan(min_liquidity=args.min_liquidity, max_spread=args.max_spread, limit=args.limit)
    print(f"Found {len(markets)} markets")
    for m in markets[:20]:
        print(f"Market: {m.question}")

if __name__ == "__main__":
    main()
