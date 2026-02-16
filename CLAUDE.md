# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kirby Gate Enforcement System — a local Python CLI/TUI application for covenant enforcement and security-fee debt collection across a 21-parcel, 672,718 SF commercial campus in Memphis, TN. Tracks covenant compliance, arrears, enforcement actions, and generates legal demand letters and Excel exports. All data is stored locally in SQLite.

## Running the Application

```bash
python kirbygate.py                          # Interactive menu-driven system (primary)
python tracker.py list                       # CLI: list all targets
python tracker.py view <id>                  # CLI: view one target
python tracker.py update <id> <field> <value># CLI: update a field
python tracker.py export [filename]          # CLI: export to CSV
python gen_demands.py                        # Batch-generate DOCX demand letters
python rebuild_db.py                         # Reset DB with seed data (destructive)
```

There are no tests, linter, or build steps. Dependencies: `python-docx`, `openpyxl`, `sqlite3` (stdlib).

## Architecture

### Source Files

- **kirbygate.py** (~1600 lines) — Main interactive menu system. Connects to `kirbygate.db`. Contains all UI, financial calculations (pro-rata shares, arrears, settlement offers), demand letter generation, Excel export (4-sheet workbook), enforcement timeline/deadline tracking, and dashboard with priority rankings.
- **tracker.py** (~350 lines) — Lightweight CLI for scripting. Uses a **separate** database `kirby_gate.db` (different schema from the main app).
- **gen_demands.py** (~370 lines) — Batch demand letter generator. Reads `kirbygate.db`, produces one DOCX per DELINQUENT parcel with entity-specific contact info, arrears breakdown, cure period, and legal references.
- **rebuild_db.py** (~300 lines) — Schema creator and seed data loader. Drops and recreates `kirbygate.db` with 21 parcels (9 CURRENT, 10 DELINQUENT, 1 DISPUTED, 1 RECON, 1 VERIFY) and the `rates` table.

### Databases

Two separate SQLite databases exist — be aware they are **not interchangeable**:

| Database | Used by | Tables |
|---|---|---|
| `kirbygate.db` (live) | kirbygate.py, gen_demands.py, rebuild_db.py | `parcels`, `enforcement_log`, `rates` |
| `kirby_gate.db` (legacy CLI) | tracker.py | different schema |

**Parcels table key fields:** id, address, business_name, sqft, pct_campus, status, entity_owner, corporate_target, past_due_balance, weekly_rate, certified_mail_tracking, date_packet_sent, cure_deadline, lien_filing_date, enforcement_step, next_action, deadline, notes.

**Status values:** CURRENT, DELINQUENT, DISPUTED, RECON, VERIFY, SETTLED.

### Key Business Constants (hardcoded)

- Total campus: 672,718 SF
- Historic weekly rate: $6,069.52 (pre-Jan 2026), current: $9,000.00
- Arrears period: 156 weeks (36 months)
- Cure period: 15 days (Declaration) / 30 days (demands)
- Lien deadline: April 1, 2026
- Declaration date: May 5, 2011; statute of limitations: 6 years
- Declarant: Walter D. Wills III (Wills & Wills LP)
- Attorney: Jeff Rosenblum

### Key Patterns

- Database paths are hardcoded as relative paths in each script (no config file).
- `kirbygate.py` initializes its own schema on startup if tables don't exist.
- Platform-aware: uses `cls`/`clear` based on OS; forces UTF-8 stdout on Windows.
- All generated output (DOCX letters, XLSX exports) is written to the project root directory.
- Foreign key constraints are explicitly enabled on each SQLite connection.
