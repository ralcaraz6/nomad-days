"""nomad-days: how many days I've spent where, and how close I am to each limit.

  nomad-days status                      where I stand today
  nomad-days plan PT 2026-12-01 2027-01-20   what a planned trip would do to my limits
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from datetime import date
from pathlib import Path

from .model import Stay, current_stay, load_trips
from .rules import Rule, check_plan, evaluate, year_counts

ROOT = Path(__file__).resolve().parents[2]


def load_rules(path: Path) -> tuple[list[Rule], dict]:
    cfg = tomllib.loads(Path(path).read_text())
    rules = [Rule(**r) for r in cfg.get("rule", [])]
    if not rules:
        raise SystemExit(f"No [[rule]] entries in {path}")
    return rules, cfg.get("settings", {})


def status(rules: list[Rule], stays: list[Stay], on: date) -> tuple[str, bool]:
    results = [evaluate(r, stays, on) for r in rules]
    w = max(len(r.name) for r in rules)
    lines = [f"nomad-days status on {on.isoformat()}", ""]
    here = current_stay(stays, on)
    if here:
        lines += [f"Now in {here.country} since {here.arrive.isoformat()} ({(on - here.arrive).days + 1} days)", ""]
    lines.append(f"{'Rule'.ljust(w)}  {'Used':>4}  {'Limit':>5}  {'Left':>4}  Status")
    for res in results:
        line = f"{res.rule.name.ljust(w)}  {res.used:>4}  {res.rule.max_days:>5}  {res.left:>4}  {res.status}"
        if res.leave_by:
            line += f"  leave by {res.leave_by.isoformat()}"
        if res.reenter_on:
            line += f"  can re-enter on {res.reenter_on.isoformat()}"
        lines.append(line)
    counts = year_counts(stays, on)
    if counts:
        lines += ["", f"Days per country in {on.year}: " + ", ".join(f"{c} {n}" for c, n in counts.items())]
    bad = any(res.status in {"OVER"} for res in results)
    return "\n".join(lines) + "\n", bad


def plan(rules: list[Rule], stays: list[Stay], trip: Stay, on: date) -> tuple[str, bool]:
    breaks = check_plan(rules, stays, trip, on)
    lines = [f"Plan: {trip.country} {trip.arrive.isoformat()} to {trip.depart.isoformat()}", ""]
    for name, day in breaks.items():
        lines.append(f"- {name}: " + (f"BREAKS on {day.isoformat()}" if day else "fine"))
    return "\n".join(lines) + "\n", any(breaks.values())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="nomad-days", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--trips", type=Path, default=Path("trips.csv"))
    p.add_argument("--rules", type=Path, default=Path("nomad.toml"))
    p.add_argument("--on", type=date.fromisoformat, help="evaluate as of this date (default: today)")
    p.add_argument("--demo", action="store_true", help="use the made-up sample trips and rules")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status")
    pp = sub.add_parser("plan")
    pp.add_argument("country")
    pp.add_argument("arrive", type=date.fromisoformat)
    pp.add_argument("depart", type=date.fromisoformat)
    args = p.parse_args(argv)

    trips, rules_path = args.trips, args.rules
    if args.demo:
        trips, rules_path = ROOT / "sample" / "trips.csv", ROOT / "sample" / "nomad.toml"
    rules, settings = load_rules(rules_path)
    on = args.on or (date.fromisoformat(settings["demo_today"]) if args.demo and "demo_today" in settings else date.today())
    stays = load_trips(trips)

    if args.cmd == "plan":
        if args.depart < args.arrive:
            raise SystemExit("depart is before arrive")
        out, bad = plan(rules, stays, Stay(args.country.upper(), args.arrive, args.depart), on)
    else:
        out, bad = status(rules, stays, on)
    sys.stdout.write(out)
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
