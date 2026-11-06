# nomad-days

I work remotely and move between countries. The questions that actually cost money are always the same: how many days have I spent in each country this year, how long can I stay where I am, and will the trip I'm planning break a visa or tax-residency limit? `nomad-days` answers them from a plain CSV of my trips.

**Who it's for:** remote workers and long-term travellers who track days for visas or tax residency.
**Built with:** Python 3.11+, standard library only. No API, no account, no network: your travel history never leaves your machine.

## What it does

```
$ nomad-days status
Now in ID since 2026-10-12 (26 days)

Rule                      Used  Limit  Left  Status
Schengen 90/180             27     90    63  ok
Indonesia stay (60 days)    26     60    34  ok  leave by 2026-12-10
Australia tax year (183)    33    183   150  ok

Days per country in 2026: AU 74, PT 42, GE 42, VN 42, TH 39, ES 27, MA 26, ID 26

$ nomad-days plan PT 2026-12-01 2027-03-15
- Schengen 90/180: BREAKS on 2027-03-01
```

Three kinds of rule, all set in a TOML file:

| Kind | Example | What it checks |
|---|---|---|
| `rolling` | Schengen 90/180 | Days in a zone within any rolling window; tells you when to leave, or when you can re-enter |
| `per_stay` | Visa on arrival, 60 days | Length of the current unbroken stay; tells you the last day you can stay |
| `yearly` | Tax residency, 183 days | Days in a country in a tax year, with a configurable start (e.g. 1 July) |

A day counts for every country you were in, so travel days count on both sides (the Schengen convention). `status` exits with code 2 when a limit is broken, so it can drive a reminder or a cron job.

## Run it

Try it with made-up trips (no setup):

```bash
git clone https://github.com/ralcaraz6/nomad-days.git
cd nomad-days
PYTHONPATH=src python3 -m nomad_days --demo status
PYTHONPATH=src python3 -m nomad_days --demo plan PT 2026-12-01 2027-03-15
```

With your own trips:

```bash
cp trips.example.csv trips.csv        # one row per stay; leave "depart" empty where you are now
cp nomad.example.toml nomad.toml      # your visa and tax rules
PYTHONPATH=src python3 -m nomad_days status
```

Both `trips.csv` and `nomad.toml` are git-ignored. Or install it with `pip install -e .` and run `nomad-days status`.

Visa and tax rules change and depend on your passport: the numbers in the example files are a starting point, not advice. Check the current official rules.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Plans

See [ROADMAP.md](ROADMAP.md): a calendar view, "earliest return" planning, reminders before a limit, imports from booking emails and calendars.

## License

MIT.
