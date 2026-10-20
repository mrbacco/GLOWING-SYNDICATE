# File:     backend/tests/test_domain.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Business rules, matching the Android app's LineCheckerTest, WeekMathTest and PhoneNumbersTest."""

from datetime import date

from app.domain import lotto, phones, text
from app.domain.ledger import balance
from app.domain.weeks import week_start, weeks_between

RULES = lotto.LOTTO_6_45
DRAW = [11, 22, 23, 33, 40, 45]
BONUS = 12


def check(*numbers: int) -> lotto.LineResult:
    return lotto.check_line(list(numbers), DRAW, BONUS, RULES)


def tier(*numbers: int) -> str | None:
    result = check(*numbers)
    return result.tier.code if result.tier else None


# ------------------------------------------------------------------- lotto


def test_counts_matches_and_bonus():
    result = check(7, 11, 12, 21, 22, 33)
    assert result.matched == {11, 22, 33}
    assert result.bonus_matched
    assert result.label == "3 numbers + bonus"
    assert result.tier.code == "MATCH_3_BONUS"


def test_labels():
    assert check(1, 2, 3, 4, 5, 6).label == "no numbers"
    assert check(1, 2, 3, 4, 5, 12).label == "the bonus ball only"
    assert check(1, 2, 3, 4, 11, 12).label == "1 number + bonus"


def test_picks_the_prize_tier():
    assert tier(11, 22, 23, 33, 40, 45) == "JACKPOT"
    assert tier(11, 22, 23, 33, 40, 12) == "MATCH_5_BONUS"
    assert tier(11, 22, 23, 33, 40, 1) == "MATCH_5"
    assert tier(7, 11, 13, 21, 22, 33) == "MATCH_3"
    assert tier(1, 11, 12, 22, 30, 31) == "MATCH_2_BONUS"


def test_no_prize_for_two_without_bonus_or_one_plus_bonus():
    assert tier(1, 11, 22, 30, 31, 32) is None
    assert tier(1, 11, 12, 30, 31, 32) is None


def test_bonus_tier_ranks_above_same_count_without_bonus():
    with_bonus, without = check(11, 22, 23, 33, 40, 12), check(11, 22, 23, 33, 40, 1)
    assert lotto.tier_rank(with_bonus, RULES) < lotto.tier_rank(without, RULES)


def test_rules_change_on_5_september_2026():
    assert lotto.rules_for(date(2026, 1, 3)).name == "Lotto 6/47"
    assert lotto.rules_for(date(2026, 9, 2)).name == "Lotto 6/47"
    assert lotto.rules_for(date(2026, 9, 5)).name == "Lotto 6/45"
    assert lotto.rules_for(date(2026, 9, 3)).name == "Lotto 6/45"  # between games: the new one
    assert lotto.LOTTO_6_45.is_draw_day(date(2026, 10, 19))  # Monday
    assert not lotto.LOTTO_6_47.is_draw_day(date(2026, 8, 31))  # no Monday draws then


def test_fixed_prizes():
    fixed = {t.code: t.fixed_prize_cents for t in RULES.tiers if t.fixed_prize_cents}
    assert fixed == {"MATCH_3": 400, "MATCH_2_BONUS": 400}


def test_validates_lines():
    assert lotto.validate_numbers([3, 12, 24, 27, 38, 41], RULES) is None
    assert lotto.validate_numbers([1, 2, 3, 4, 5], RULES)  # too few
    assert lotto.validate_numbers([1, 2, 3, 4, 5, 5], RULES)  # duplicate
    assert lotto.validate_numbers([1, 2, 3, 4, 5, 46], RULES)  # 45 balls since Sep 2026
    assert lotto.validate_numbers([1, 2, 3, 4, 5, 46], lotto.LOTTO_6_47) is None


# ------------------------------------------------------- weeks and payments


def test_weeks_start_on_monday():
    assert week_start(date(2026, 10, 25)) == date(2026, 10, 19)  # Sunday
    assert week_start(date(2026, 10, 19)) == date(2026, 10, 19)


def test_weeks_between_includes_both_ends():
    assert weeks_between(date(2026, 10, 8), date(2026, 10, 20)) == [
        date(2026, 10, 5),
        date(2026, 10, 12),
        date(2026, 10, 19),
    ]


def test_balance():
    joined, today = date(2026, 10, 5), date(2026, 10, 20)
    b = balance(joined, {date(2026, 10, 5)}, 500, today)
    assert (b.paid_this_week, b.weeks_owed, b.amount_owed_cents) == (False, 2, 1000)
    assert balance(joined, {date(2026, 10, 5), date(2026, 10, 12), date(2026, 10, 19)}, 500, today).weeks_owed == 0


# -------------------------------------------------------------- text, phones


def test_text():
    assert text.euro(500) == "€5.00"
    assert text.euro(1505) == "€15.05"
    assert text.draw_date(date(2026, 10, 19)) == "Mon 19 Oct 2026"
    assert text.member_message("Seán", "Office", 1000, "http://x/m/t") == (
        "Hi Seán, a quick reminder for Office: you owe €10.00. Thanks! Your page: http://x/m/t"
    )
    assert text.member_message("Aoife", "Office", 0, "http://x/m/t").endswith("our results: http://x/m/t")


def test_phones():
    assert phones.international("087 123 4567") == "353871234567"
    assert phones.international("+353 87 123 4567") == "353871234567"
    assert phones.international("0044 7700 900123") == "447700900123"
    assert phones.international("call me") is None
    assert phones.international("12345") is None
