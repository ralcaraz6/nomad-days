# Roadmap

What I plan to build next, roughly in order. Estimates are honest guesses.

## Done (v0.1)
- [x] Trips in a CSV, rules in TOML (rolling window, per stay, yearly with custom year start)
- [x] `status`: days used and left per rule, "leave by" date where I am, "can re-enter on" when I'm out of days
- [x] `plan`: what a planned trip does to each rule, and the first day it breaks
- [x] Days per country this year
- [x] `--demo` with made-up trips, unit tests, CI on every push

## Next: plan trips with it (~9 h)
- [ ] `plan` with several legs at once (a whole itinerary from a file) — 3 h
- [ ] `max-stay COUNTRY DATE`: longest trip I can take starting on a date — 2 h
- [ ] `add` / `leave` commands so I never edit the CSV by hand — 2 h
- [ ] Validate overlapping or impossible stays with clear errors — 2 h

## Then: see it and get reminded (~10 h)
- [ ] Calendar view of the year in the terminal, coloured by country — 3 h
- [ ] HTML report I can keep as a record for a tax advisor — 3 h
- [ ] Reminder N days before a limit (cron-friendly output, optional Telegram message) — 3 h
- [ ] Export days per country as CSV for a tax year — 1 h

## Later: less typing (~10 h)
- [ ] Import stays from an .ics calendar export (flights as events) — 4 h
- [ ] Import from forwarded flight confirmation emails (.eml files) — 4 h
- [ ] Rule presets for common visas, each with a link to the official source — 2 h

Out of scope on purpose: storing anyone else's data or sending my travel history anywhere. Everything stays local.
