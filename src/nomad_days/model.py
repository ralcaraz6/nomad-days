"""Trips and day presence. A day counts for every country you were in, travel days included."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

# Schengen area members (29 since Bulgaria and Romania joined fully in 2025).
SCHENGEN = {
    "AT", "BE", "BG", "HR", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IS", "IT", "LV",
    "LI", "LT", "LU", "MT", "NL", "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "CH",
}
ALIASES = {"SCHENGEN": SCHENGEN}


@dataclass
class Stay:
    country: str
    arrive: date
    depart: date | None = None  # None = still there
    planned: bool = False

    def last_day(self, today: date) -> date:
        return self.depart or today


def expand(countries: list[str]) -> set[str]:
    out: set[str] = set()
    for c in countries:
        out |= ALIASES.get(c.upper(), {c.upper()})
    return out


def load_trips(path: Path) -> list[Stay]:
    stays = []
    with open(path, newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            try:
                arrive = date.fromisoformat(row["arrive"].strip())
                dep = (row.get("depart") or "").strip()
                depart = date.fromisoformat(dep) if dep else None
            except (KeyError, ValueError) as e:
                raise SystemExit(f"{path}, line {i}: bad date ({e})")
            if depart and depart < arrive:
                raise SystemExit(f"{path}, line {i}: depart is before arrive")
            stays.append(Stay(row["country"].strip().upper(), arrive, depart))
    stays.sort(key=lambda s: s.arrive)
    ongoing = [s for s in stays if s.depart is None]
    if len(ongoing) > 1:
        raise SystemExit(f"{path}: only one stay can have an empty depart date")
    return stays


def presence(stays: list[Stay], today: date) -> dict[date, set[str]]:
    days: dict[date, set[str]] = {}
    for s in stays:
        d, end = s.arrive, s.last_day(today)
        while d <= end:
            days.setdefault(d, set()).add(s.country)
            d += timedelta(days=1)
    return days


def current_stay(stays: list[Stay], on: date) -> Stay | None:
    here = [s for s in stays if s.arrive <= on <= s.last_day(on) and not s.planned]
    return max(here, key=lambda s: s.arrive) if here else None
