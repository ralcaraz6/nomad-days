import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nomad_days.cli import load_rules, main  # noqa: E402
from nomad_days.model import Stay, load_trips  # noqa: E402
from nomad_days.rules import Rule, check_plan, evaluate  # noqa: E402

D = date.fromisoformat
SCHENGEN = Rule("Schengen 90/180", "rolling", ["SCHENGEN"], 90, window_days=180)


class SchengenTests(unittest.TestCase):
    def test_entry_and_exit_days_both_count(self):
        stays = [Stay("FR", D("2026-01-01"), D("2026-01-10"))]
        self.assertEqual(evaluate(SCHENGEN, stays, D("2026-01-10")).used, 10)

    def test_ninety_first_day_breaks(self):
        trip = Stay("PT", D("2026-01-01"), D("2026-04-30"))
        breaks = check_plan([SCHENGEN], [], trip, D("2025-12-01"))
        self.assertEqual(breaks["Schengen 90/180"], D("2026-01-01") + timedelta(days=90))

    def test_days_roll_out_of_the_window(self):
        stays = [Stay("ES", D("2026-01-01"), D("2026-03-31"))]  # exactly 90 days
        self.assertEqual(evaluate(SCHENGEN, stays, D("2026-06-29")).used, 90)
        self.assertEqual(evaluate(SCHENGEN, stays, D("2026-06-30")).used, 89)

    def test_outside_and_out_of_days_means_wait(self):
        stays = [Stay("ES", D("2026-01-01"), D("2026-03-31")), Stay("MA", D("2026-03-31"), None)]
        res = evaluate(SCHENGEN, stays, D("2026-04-10"))
        self.assertEqual(res.status, "WAIT")
        self.assertEqual(res.reenter_on, D("2026-06-30"))

    def test_leave_by_while_inside(self):
        stays = [Stay("IT", D("2026-01-01"), None)]
        res = evaluate(SCHENGEN, stays, D("2026-02-01"))
        self.assertEqual(res.leave_by, D("2026-03-31"))


class OtherRuleTests(unittest.TestCase):
    def test_per_stay_resets_after_leaving(self):
        rule = Rule("ID 60", "per_stay", ["ID"], 60)
        stays = [Stay("ID", D("2026-01-01"), D("2026-02-20")), Stay("SG", D("2026-02-20"), D("2026-02-22")),
                 Stay("ID", D("2026-02-23"), None)]
        res = evaluate(rule, stays, D("2026-03-01"))
        self.assertEqual(res.used, 7)
        self.assertEqual(res.leave_by, D("2026-04-23"))

    def test_yearly_uses_custom_year_start(self):
        rule = Rule("AU tax", "yearly", ["AU"], 183, year_start="07-01")
        stays = [Stay("AU", D("2026-06-01"), D("2026-07-10"))]
        self.assertEqual(evaluate(rule, stays, D("2026-08-01")).used, 10)

    def test_yearly_plan_flags_the_day_threshold_is_reached(self):
        rule = Rule("ES tax", "yearly", ["ES"], 183)
        stays = [Stay("ES", D("2026-01-01"), D("2026-06-01"))]  # 152 days
        breaks = check_plan([rule], stays, Stay("ES", D("2026-09-01"), D("2026-12-31")), D("2026-08-01"))
        self.assertEqual(breaks["ES tax"], D("2026-10-01"))


class DemoTests(unittest.TestCase):
    def test_demo_runs_and_files_parse(self):
        rules, settings = load_rules(ROOT / "sample" / "nomad.toml")
        self.assertEqual(len(rules), 3)
        self.assertEqual(len(load_trips(ROOT / "sample" / "trips.csv")), 9)
        self.assertEqual(main(["--demo", "status"]), 0)
        self.assertEqual(main(["--demo", "plan", "PT", "2026-12-01", "2027-03-15"]), 2)


if __name__ == "__main__":
    unittest.main()
