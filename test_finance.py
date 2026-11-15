from decimal import Decimal
from pathlib import Path

from finance import (
    INTRO,
    LineItem,
    amortize,
    invoice_total,
    late_fee,
    loan_payment,
    main,
    money,
)


def test_intro_names_the_project_and_sponsor():
    assert "spin-finance" in INTRO
    assert "Joshua Almeida" in INTRO
    assert "https://github.com/sponsors/fitzyracing1" in INTRO


def test_help_is_zero():
    assert main([]) == 0
    assert main(["--help"]) == 0


def test_money_rounds_half_up_to_cents():
    assert money("1.234") == Decimal("1.23")
    assert money("1.235") == Decimal("1.24")
    assert money("1.225") == Decimal("1.23")


def test_invoice_with_tax():
    result = invoice_total(
        [
            LineItem("Widget", Decimal("3"), Decimal("10.00")),
            LineItem("Fee", Decimal("1"), Decimal("2.50")),
        ],
        Decimal("0.08"),
    )
    assert result["subtotal"] == Decimal("32.50")
    assert result["tax"] == Decimal("2.60")
    assert result["total"] == Decimal("35.10")


def test_invoice_cli(capsys):
    assert main(["invoice", "--item", "Widget,3,10.00", "--item", "Fee,1,2.50", "--tax", "8%"]) == 0
    out = capsys.readouterr().out
    assert "32.50" in out
    assert "2.60" in out
    assert "35.10" in out


def test_invoice_csv(tmp_path, capsys):
    path = tmp_path / "items.csv"
    path.write_text("description,quantity,unit_price\nA,2,5.00\nB,1,1.25\n")
    assert main(["invoice", "--csv", str(path)]) == 0
    assert "11.25" in capsys.readouterr().out


def test_late_fee_annual_simple_interest():
    result = late_fee("1000", "15", annual_rate="0.18", year_days=365)
    # 1000 * 0.18 * 15 / 365 = 7.397... -> 7.40
    assert result["fee"] == Decimal("7.40")
    assert result["due"] == Decimal("1007.40")


def test_late_fee_monthly_thirty_day_month():
    result = late_fee("1000", "45", monthly_rate="0.015", month_days=30)
    # 1000 * 0.015 * 45/30 = 22.50
    assert result["fee"] == Decimal("22.50")


def test_late_fee_flat_and_daily():
    assert late_fee("1000", "10", flat="25")["fee"] == Decimal("25.00")
    assert late_fee("1000", "10", daily_rate="0.001")["fee"] == Decimal("10.00")


def test_late_fee_cli(capsys):
    assert main(["late-fee", "--principal", "1000", "--annual-rate", "0.18", "--days", "15"]) == 0
    assert "7.40" in capsys.readouterr().out


def test_loan_payment_matches_known_value():
    # Excel/standard PMT(0.05/12, 36, -10000) = 299.70898... -> 299.71
    assert loan_payment("10000", "0.05", 36) == Decimal("299.71")


def test_zero_rate_loan_splits_evenly():
    assert loan_payment("100.00", "0", 4) == Decimal("25.00")


def test_amortization_clears_the_balance():
    rows = amortize("10000", "0.05", 36)
    assert rows[0]["payment"] == Decimal("299.71")
    assert rows[-1]["balance"] == Decimal("0.00")
    paid_principal = sum((row["principal"] for row in rows), Decimal("0"))
    assert paid_principal == Decimal("10000.00")


def test_loan_cli(capsys):
    assert main(["loan", "--principal", "10000", "--annual-rate", "0.05", "--term", "36"]) == 0
    assert "299.71" in capsys.readouterr().out


def test_rejects_empty_invoice():
    assert main(["invoice", "--tax", "0.08"]) == 2


def test_rejects_two_late_fee_rates():
    assert main(
        ["late-fee", "--principal", "1000", "--days", "10", "--flat", "5", "--annual-rate", "0.1"]
    ) == 2
