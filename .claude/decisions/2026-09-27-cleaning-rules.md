# Cleaning rules for Task 02

**Date:** 2026-09-27
**Made by:** assistant (autonomous — user did not specify these details)
**Status:** active

## Context
Implementing `src/cleaning.py` and `scripts/02_clean_data.py` required several concrete choices the methodology note left open.

## Decisions and rationale
| Choice | Alternative rejected | Why |
|---|---|---|
| Master calendar = dates on which SPY actually traded | Generic business days / US federal holiday calendar | Federal calendars get NYSE-specific holidays wrong (e.g. Good Friday is an NYSE holiday, Veterans Day is not). SPY's real dates are the exact NYSE calendar. |
| Crypto weekend rows dropped, returns computed **after** alignment | Computing crypto returns on the 7-day grid first | Monday's crypto return then spans Friday→Monday, so the weekend move is kept, not lost. |
| Forward-fill internal gaps of ≤ 2 trading days | 1 day (as in the draft note) | Covers a single bad quote plus an adjacent one; still too short to hide a real event. |
| Gaps > 2 days left as NaN and listed in `cleaning_log.txt` | Filling them | A multi-day gap usually means a halt, delisting or ticker change; hiding it would be wrong. |
| Volume aligned but never filled | Forward-filling volume | A missing volume day is not "unchanged volume". |
| Save simple and log daily returns as separate files | One file with MultiIndex columns | Simpler for a first project; downstream code loads the one it needs. |

## Consequences
With the current data, no fills or long gaps occurred (every equity traded on every SPY date; crypto trades daily). The rules matter if the universe or date range changes.
