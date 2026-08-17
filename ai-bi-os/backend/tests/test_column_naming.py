"""Tests that a column's name style does not decide whether the dashboard works.

Every rule that identifies columns here uses word-boundary regexes, and `\\b`
has no boundary to find inside camelCase. So "TransactionDate" read as
"transactiondate", `\\bdate\\b` could not match, and a column whose 3,662
values were all valid dates was classified as not a date.

That was not a cosmetic miss. No date column means no time series, so the
dashboard's main chart rendered as a flat zero with "No data for this period"
across a frame containing twelve months. And "TransactionRef" was missed the
same way, so the entity being counted fell back to the date column - "Total
Transactions" reported 324, which is how many distinct *days* the 3,662
transactions fell on, sitting on the same screen as a card reading 3,662.
"""

import pandas as pd
import pytest

from app.services.semantic_classification import (
    col_words,
    looks_like_dates,
    fallback_classify,
)
from app.services.stats_service import compute_kpis


@pytest.fixture
def bank_df():
    """Shaped like the file that exposed this: camelCase throughout."""
    dates = pd.date_range("2025-07-01", periods=360, freq="D").strftime("%Y-%m-%d")
    return pd.DataFrame({
        "TransactionDate": list(dates) * 2,
        "TransactionRef": [f"UTR{i:06d}" for i in range(720)],
        "AccountHolder": ["A. Person"] * 720,
        "TransactionType": ["UPI", "IMPS"] * 360,
        "Amount": [100.0, -50.0] * 360,
        "Status": ["Cleared"] * 720,
    })


# ── the splitter ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("TransactionDate", "transaction date"),
    ("TransactionRef", "transaction ref"),
    ("order_date", "order date"),
    ("order-date", "order date"),
    ("OrderID", "order id"),          # trailing acronym stays whole
    ("UTRNumber", "utr number"),      # leading acronym stays whole
    ("amount", "amount"),
    ("created_at", "created at"),
])
def test_names_reduce_to_words(name, expected):
    assert col_words(name) == expected


def test_the_regexes_that_failed_now_match():
    import re
    # This exact match is what the whole chart depended on.
    assert re.search(r"\bdate\b", col_words("TransactionDate"))
    assert re.search(r"\bref\b", col_words("TransactionRef"))
    # And it must not start matching things that are not dates.
    assert not re.search(r"\bdate\b", col_words("Candidate"))
    assert not re.search(r"\bdate\b", col_words("UpdateCount"))


# ── asking the data instead of the name ──────────────────────────────────────

def test_a_date_column_is_recognised_by_its_values(bank_df):
    assert looks_like_dates(bank_df["TransactionDate"]) is True


def test_columns_that_are_not_dates_are_left_alone(bank_df):
    assert looks_like_dates(bank_df["Amount"]) is False
    assert looks_like_dates(bank_df["AccountHolder"]) is False
    # Numbers are excluded deliberately: a year-like integer or an amount
    # would otherwise parse and be misread as a timestamp.
    assert looks_like_dates(pd.Series([2024, 2025, 2026] * 10)) is False


def test_an_oddly_named_date_column_is_still_found():
    # No rule anticipates "Posted" - the values have to be what decides.
    posted = pd.Series(pd.date_range("2025-01-01", periods=50).strftime("%Y-%m-%d"))
    assert looks_like_dates(posted) is True


def test_an_empty_or_broken_column_is_not_a_date():
    assert looks_like_dates(pd.Series([None] * 10)) is False
    assert looks_like_dates(pd.Series(["not a date"] * 10)) is False


# ── what the user actually sees ──────────────────────────────────────────────

def test_the_date_column_is_classified_as_one(bank_df):
    _, sem = fallback_classify(bank_df, "bank_statement.csv")
    assert sem["semantic_dictionary"]["date_columns"] == ["TransactionDate"]


def test_transactions_are_counted_by_reference_not_by_day(bank_df):
    _, sem = fallback_classify(bank_df, "bank_statement.csv")
    entity = sem["business_terminology"]["entity_col"]
    # Counting distinct dates and calling it "Total Transactions" reported 324
    # for 3,662 transactions - the number of days they landed on.
    assert entity == "TransactionRef"
    assert bank_df[entity].nunique() == len(bank_df)


def test_the_chart_has_points(bank_df):
    _, sem = fallback_classify(bank_df, "bank_statement.csv")
    result = compute_kpis(bank_df.copy(), sem)
    # The symptom was an empty list rendered as "No data for this period".
    assert len(result["chart_data"]) > 0
    assert all("name" in p and "value" in p for p in result["chart_data"])


def test_a_dataset_stored_with_the_old_broken_classification_still_charts(bank_df):
    # Datasets classified before the fix have an empty date_columns list saved
    # against them. Making everyone re-upload to get their chart back is not a
    # fix, so the read path asks the frame when the stored dictionary is empty.
    stale = {
        "domain": "banking",
        "semantic_dictionary": {"date_columns": [], "numeric_metrics": ["Amount"]},
        "business_terminology": {
            "primary_metric": "Amount",
            "primary_metric_op": "sum",
            "entity_col": "TransactionDate",
        },
    }
    result = compute_kpis(bank_df.copy(), stale)
    assert len(result["chart_data"]) > 0
