import argparse
from data.scanner import run_scan

def main() -> None:
    parser = argparse.ArgumentParser(description="Desktop Tutorial Scanner")
    parser.add_argument("command", nargs="?", default="scan", choices=["scan", "status"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "status":
        print("Scanner is ready")
        return

    markets = run_scan()
    print(f"Found {len(markets)} markets")
    for m in markets[:20]:
        print(f"Market: {m.question}")

if __name__ == "__main__":
    main()
