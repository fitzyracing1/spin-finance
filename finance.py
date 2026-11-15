"""spin-finance: invoice, late-fee, and loan math with exact Decimal cents."""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

INTRO = (
    "spin-finance by Joshua Almeida.\n"
    "Exact Decimal math, no API, offline. Sponsor: https://github.com/sponsors/fitzyracing1"
)

CENTS = Decimal("0.01")
ZERO = Decimal("0")


def D(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text.endswith("%"):
        return Decimal(text[:-1].strip()) / Decimal("100")
    return Decimal(text)


def money(value) -> Decimal:
    return D(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def fmt(value: Decimal) -> str:
    return f"{money(value):.2f}"


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: Decimal
    unit_price: Decimal

    def extension(self) -> Decimal:
        return money(self.quantity * self.unit_price)


def invoice_total(
    items: Iterable[LineItem], tax_rate: Decimal = ZERO
) -> dict:
    lines = list(items)
    if not lines:
        raise ValueError("Invoice needs at least one line item.")
    if tax_rate < ZERO:
        raise ValueError("Tax rate cannot be negative.")
    subtotal = sum((line.extension() for line in lines), ZERO)
    tax = money(subtotal * tax_rate)
    total = money(subtotal + tax)
    return {
        "lines": lines,
        "subtotal": money(subtotal),
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
    }


def late_fee(
    principal,
    days,
    *,
    annual_rate=None,
    daily_rate=None,
    monthly_rate=None,
    flat=None,
    year_days=365,
    month_days=30,
) -> dict:
    principal = D(principal)
    days = D(days)
    if principal < ZERO:
        raise ValueError("Principal cannot be negative.")
    if days < ZERO:
        raise ValueError("Days late cannot be negative.")
    specified = [v is not None for v in (annual_rate, daily_rate, monthly_rate, flat)]
    if sum(specified) != 1:
        raise ValueError("Give exactly one of --annual-rate, --daily-rate, --monthly-rate, or --flat.")
    if flat is not None:
        fee = money(flat)
        method = "flat amount"
        rate_note = f"flat {fmt(fee)}"
    elif daily_rate is not None:
        fee = money(principal * D(daily_rate) * days)
        method = "daily rate * days"
        rate_note = f"daily rate {D(daily_rate)}"
    elif monthly_rate is not None:
        fee = money(principal * D(monthly_rate) * (days / D(month_days)))
        method = "monthly rate * (days / month_days)"
        rate_note = f"monthly rate {D(monthly_rate)}, month_days={month_days}"
    else:
        fee = money(principal * D(annual_rate) * (days / D(year_days)))
        method = "simple interest, annual_rate * days / year_days"
        rate_note = f"annual rate {D(annual_rate)}, year_days={year_days}"
    return {
        "principal": money(principal),
        "days": days,
        "fee": fee,
        "due": money(principal + fee),
        "method": method,
        "rate_note": rate_note,
    }


def loan_payment(principal, annual_rate, term, payments_per_year=12) -> Decimal:
    principal = D(principal)
    annual_rate = D(annual_rate)
    term = int(term)
    payments_per_year = int(payments_per_year)
    if principal < ZERO:
        raise ValueError("Principal cannot be negative.")
    if annual_rate < ZERO:
        raise ValueError("Annual rate cannot be negative.")
    if term <= 0:
        raise ValueError("Term must be a positive number of payments.")
    if payments_per_year <= 0:
        raise ValueError("Payments per year must be positive.")
    if annual_rate == ZERO:
        return money(principal / Decimal(term))
    r = annual_rate / Decimal(payments_per_year)
    factor = (Decimal("1") + r) ** term
    payment = principal * r * factor / (factor - Decimal("1"))
    return money(payment)


def amortize(principal, annual_rate, term, payments_per_year=12) -> list[dict]:
    principal = money(principal)
    payment = loan_payment(principal, annual_rate, term, payments_per_year)
    r = D(annual_rate) / Decimal(int(payments_per_year))
    balance = principal
    rows = []
    for n in range(1, int(term) + 1):
        interest = money(balance * r) if r != ZERO else ZERO
        if n == int(term):
            principal_paid = balance
            paid = money(principal_paid + interest)
        else:
            principal_paid = money(payment - interest)
            if principal_paid > balance:
                principal_paid = balance
            paid = payment
        balance = money(balance - principal_paid)
        if balance < ZERO:
            balance = ZERO
        rows.append(
            {
                "n": n,
                "payment": paid,
                "interest": interest,
                "principal": principal_paid,
                "balance": balance,
            }
        )
    return rows


def _parse_item(text: str) -> LineItem:
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 3:
        raise ValueError("Each --item must be description,quantity,unit_price")
    return LineItem(parts[0], D(parts[1]), D(parts[2]))


def _items_from_csv(path: str) -> list[LineItem]:
    items = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"description", "quantity", "unit_price"}
        if reader.fieldnames is None or not required.issubset({n.strip() for n in reader.fieldnames}):
            raise ValueError("Invoice CSV needs description,quantity,unit_price columns.")
        for row in reader:
            items.append(
                LineItem(
                    row["description"].strip(),
                    D(row["quantity"]),
                    D(row["unit_price"]),
                )
            )
    return items


def _print_invoice(result: dict) -> None:
    print(INTRO)
    print()
    print("Invoice  (amounts rounded half-up to cents)")
    for line in result["lines"]:
        print(
            f"  {line.description:<24} {line.quantity} x {fmt(line.unit_price)}"
            f"  = {fmt(line.extension())}"
        )
    print(f"  {'subtotal':<24} {fmt(result['subtotal'])}")
    print(f"  tax @ {result['tax_rate']}            {fmt(result['tax'])}")
    print(f"  {'total':<24} {fmt(result['total'])}")


def _print_late_fee(result: dict) -> None:
    print(INTRO)
    print()
    print("Late fee  (simple interest or flat, rounded half-up to cents)")
    print(f"  principal     {fmt(result['principal'])}")
    print(f"  days late     {result['days']}")
    print(f"  method        {result['method']}")
    print(f"  rate          {result['rate_note']}")
    print(f"  fee           {fmt(result['fee'])}")
    print(f"  amount due    {fmt(result['due'])}")


def _print_loan(principal, annual_rate, term, payments_per_year, schedule: bool) -> None:
    payment = loan_payment(principal, annual_rate, term, payments_per_year)
    print(INTRO)
    print()
    print("Loan  (fixed payment, rounded half-up to cents; last payment adjusted)")
    print(f"  principal           {fmt(D(principal))}")
    print(f"  annual rate         {D(annual_rate)}")
    print(f"  payments            {term} at {payments_per_year}/year")
    print(f"  payment             {fmt(payment)}")
    if schedule:
        rows = amortize(principal, annual_rate, term, payments_per_year)
        interest_total = sum((row["interest"] for row in rows), ZERO)
        print(f"  total interest      {fmt(interest_total)}")
        print(f"  {'n':>4}  {'payment':>10}  {'interest':>10}  {'principal':>10}  {'balance':>10}")
        for row in rows:
            print(
                f"  {row['n']:4d}  {fmt(row['payment']):>10}  {fmt(row['interest']):>10}"
                f"  {fmt(row['principal']):>10}  {fmt(row['balance']):>10}"
            )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="finance.py",
        description="Invoice, late-fee, and loan payment calculator using Decimal cents.",
    )
    sub = parser.add_subparsers(dest="cmd")

    inv = sub.add_parser("invoice", help="Sum line items and optional tax.")
    inv.add_argument("--item", action="append", default=[], help="description,quantity,unit_price")
    inv.add_argument("--csv", help="CSV with description,quantity,unit_price columns.")
    inv.add_argument("--tax", default="0", help="Tax rate, such as 0.08 or 8%.")

    late = sub.add_parser("late-fee", help="Simple-interest or flat late fee.")
    late.add_argument("--principal", required=True)
    late.add_argument("--days", required=True)
    late.add_argument("--annual-rate", dest="annual_rate")
    late.add_argument("--daily-rate", dest="daily_rate")
    late.add_argument("--monthly-rate", dest="monthly_rate")
    late.add_argument("--flat")
    late.add_argument("--year-days", dest="year_days", default="365")
    late.add_argument("--month-days", dest="month_days", default="30")

    loan = sub.add_parser("loan", help="Fixed loan payment and optional amortization.")
    loan.add_argument("--principal", required=True)
    loan.add_argument("--annual-rate", dest="annual_rate", required=True)
    loan.add_argument("--term", required=True, help="Number of payments.")
    loan.add_argument("--payments-per-year", dest="ppy", default="12")
    loan.add_argument("--amortization", action="store_true")

    try:
        args = parser.parse_args([] if argv is None and len(sys.argv) == 1 else (sys.argv[1:] if argv is None else argv))
    except SystemExit as exc:
        code = exc.code
        return 0 if code in (0, None) else int(code)

    if not args.cmd:
        print(INTRO)
        print()
        print("Usage: python finance.py invoice --item 'Widget,3,10.00' --tax 8%")
        print("       python finance.py late-fee --principal 1000 --annual-rate 0.18 --days 15")
        print("       python finance.py loan --principal 10000 --annual-rate 0.05 --term 36 --amortization")
        return 0
    try:
        if args.cmd == "invoice":
            items = [_parse_item(raw) for raw in args.item]
            if args.csv:
                items.extend(_items_from_csv(args.csv))
            result = invoice_total(items, D(args.tax))
            _print_invoice(result)
            return 0
        if args.cmd == "late-fee":
            result = late_fee(
                args.principal,
                args.days,
                annual_rate=args.annual_rate,
                daily_rate=args.daily_rate,
                monthly_rate=args.monthly_rate,
                flat=args.flat,
                year_days=int(args.year_days),
                month_days=int(args.month_days),
            )
            _print_late_fee(result)
            return 0
        _print_loan(args.principal, args.annual_rate, int(args.term), int(args.ppy), args.amortization)
        return 0
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
