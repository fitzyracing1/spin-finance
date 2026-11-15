"""spin-finance: Invoice totals, late fees, and loan payments with exact Decimal math"""
import sys

INTRO = (
    "spin-finance by Joshua Almeida.\n"
    "The calculator ships in a pull request. It will compute invoices, late fees, and loan amortizations in cents, with no floating-point money.\n"
    "Sponsor: https://github.com/sponsors/fitzyracing1"
)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    print(INTRO)
    if argv and argv[0] in ("-h", "--help", "help"):
        print()
        print("Usage: python finance.py")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
