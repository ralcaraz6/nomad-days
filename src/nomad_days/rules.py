"""Day-limit rules: rolling windows (Schengen 90/180), per-stay limits (visa on arrival),
and yearly counts (tax residency thresholds)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .model import Stay, current_stay, expand, presence

MAX_LOOKAHEAD = 400


@dataclass
class Rule:
    name: str
    kind: str                      # "rolling" | "per_stay" | "yearly"
    countries: list[str]
    max_days: int
    window_days: int = 180         # rolling only
    year_start: str = "01-01"      # yearly only, MM-DD (e.g. "07-01" for an Australian tax year)
    warn_days: int = 10            # warn when this many days or fewer are left
    zone: set[str] = field(init=False)

    def __post_init__(self):
        if self.kind not in {"rolling", "per_stay", "yearly"}:
            raise SystemExit(f"Rule '{self.name}': unknown kind '{self.kind}'")
        self.zone = expand(self.countries)


@dataclass
class Result:
    rule: Rule
    used: int
    leave_by: date | None = None
    reenter_on: date | None = None   # rolling rules, when I'm outside the zone and out of days

    @property
    def left(self) -> int:
        return self.rule.max_days - self.used

    @property
    def status(self) -> str:
        if self.reenter_on:
            return "WAIT"
        if self.rule.kind == "yearly":
            if self.used >= self.rule.max_days:
                return "REACHED"
        elif self.used > self.rule.max_days:
            return "OVER"
        return "WARN" if self.left <= self.rule.warn_days else "ok"


def _in_zone(days: dict[date, set[str]], d: date, zone: set[str]) -> bool:
    return bool(days.get(d, set()) & zone)


def _rolling_used(days, zone, end: date, window: int) -> int:
    return sum(_in_zone(days, end - timedelta(days=i), zone) for i in range(window))


def _year_start(rule: Rule, on: date) -> date:
    m, d = (int(x) for x in rule.year_start.split("-"))
    start = date(on.year, m, d)
    return start if start <= on else date(on.year - 1, m, d)


def _stay_start(days, zone, on: date) -> date | None:
    """First day of the unbroken run of days in the zone that includes `on`."""
    if not _in_zone(days, on, zone):
        return None
    d = on
    while _in_zone(days, d - timedelta(days=1), zone):
        d -= timedelta(days=1)
    return d


def used_on(rule: Rule, days, on: date) -> int:
    if rule.kind == "rolling":
        return _rolling_used(days, rule.zone, on, rule.window_days)
    if rule.kind == "per_stay":
        start = _stay_start(days, rule.zone, on)
        return 0 if start is None else (on - start).days + 1
    start = _year_start(rule, on)
    return sum(_in_zone(days, start + timedelta(days=i), rule.zone) for i in range((on - start).days + 1))


def evaluate(rule: Rule, stays: list[Stay], on: date) -> Result:
    days = presence(stays, on)
    res = Result(rule, used_on(rule, days, on))
    here = current_stay(stays, on)
    if rule.kind != "yearly" and here and here.depart is None and here.country in rule.zone:
        res.leave_by = latest_exit(rule, days, on)
    if rule.kind == "rolling" and not _in_zone(days, on, rule.zone) and res.used + 1 > rule.max_days:
        res.reenter_on = earliest_entry(rule, days, on)
    return res


def earliest_entry(rule: Rule, days, on: date) -> date | None:
    """First future day on which entering the zone (for at least one day) is allowed again."""
    d = on
    for _ in range(MAX_LOOKAHEAD):
        d += timedelta(days=1)
        if _rolling_used(days, rule.zone, d, rule.window_days) + 1 <= rule.max_days:
            return d
    return None


def latest_exit(rule: Rule, days, on: date) -> date | None:
    """If I stay put from `on`, the last day I can still be in the zone without breaking the rule."""
    days = {d: set(c) for d, c in days.items()}
    country = next(iter(days.get(on, set()) & rule.zone), None)
    if country is None:
        return None
    last_ok = on if used_on(rule, days, on) <= rule.max_days else None
    d = on
    for _ in range(MAX_LOOKAHEAD):
        d += timedelta(days=1)
        days.setdefault(d, set()).add(country)
        if used_on(rule, days, d) > rule.max_days:
            return last_ok
        last_ok = d
    return None  # no limit hit within the lookahead


def check_plan(rules: list[Rule], stays: list[Stay], plan: Stay, on: date) -> dict[str, date | None]:
    """For each rule, the first day of the planned stay that breaks it (None = fine)."""
    plan.planned = True
    days = presence(stays + [plan], on)
    out: dict[str, date | None] = {}
    for rule in rules:
        out[rule.name] = None
        if plan.country not in rule.zone:
            continue
        yearly = rule.kind == "yearly"
        if yearly and used_on(rule, days, plan.arrive - timedelta(days=1)) >= rule.max_days:
            continue  # threshold already reached before this trip
        d = plan.arrive
        while d <= plan.depart:
            used = used_on(rule, days, d)
            if (used >= rule.max_days) if yearly else (used > rule.max_days):
                out[rule.name] = d
                break
            d += timedelta(days=1)
    return out


def year_counts(stays: list[Stay], on: date) -> dict[str, int]:
    days = presence(stays, on)
    counts: dict[str, int] = {}
    for d, cs in days.items():
        if d.year == on.year and d <= on:
            for c in cs:
                counts[c] = counts.get(c, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))
