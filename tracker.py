#!/usr/bin/env python3
"""Kirby Gate — Covenant Enforcement Tracker

Usage:
    python tracker.py list                       Show all targets as a table
    python tracker.py view <id>                  Show full detail for one target
    python tracker.py update <id> <field> <val>  Update a field on a target
    python tracker.py export [filename.csv]      Export to CSV
    python tracker.py fields                     List updatable field names
    python tracker.py help                       Show this help
"""

import argparse
import csv
import os
import sqlite3
import sys
import textwrap
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kirby_gate.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name            TEXT NOT NULL,
    property_address       TEXT,
    contact_name           TEXT,
    contact_title          TEXT,
    corporate_address      TEXT,
    past_due_balance       REAL DEFAULT 0,
    weekly_rate            REAL DEFAULT 0,
    certified_mail_tracking TEXT,
    date_packet_sent       TEXT,
    response_deadline      TEXT,
    lien_filing_date       TEXT,
    attorney_assigned      TEXT,
    status                 TEXT DEFAULT 'not started',
    notes                  TEXT
);
"""

VALID_STATUSES = [
    "not started",
    "packet sent",
    "response received",
    "in negotiation",
    "lien filed",
    "resolved",
]

FIELD_NAMES = [
    "entity_name",
    "property_address",
    "contact_name",
    "contact_title",
    "corporate_address",
    "past_due_balance",
    "weekly_rate",
    "certified_mail_tracking",
    "date_packet_sent",
    "response_deadline",
    "lien_filing_date",
    "attorney_assigned",
    "status",
    "notes",
]

SEED_DATA = [
    {
        "entity_name": "Kroger",
        "property_address": "2835 Kirby Pkwy",
        "contact_name": "Delta Division HQ",
        "contact_title": None,
        "corporate_address": "800 Ridge Lake Blvd, Memphis, TN 38120",
        "past_due_balance": 41235.10,
        "weekly_rate": 783.90,
        "status": "not started",
    },
    {
        "entity_name": "Starbucks",
        "property_address": "2801 Kirby Pkwy",
        "contact_name": None,
        "contact_title": None,
        "corporate_address": None,
        "past_due_balance": 5254.99,
        "weekly_rate": 99.90,
        "status": "not started",
    },
    {
        "entity_name": "Wendy's",
        "property_address": "2845 Kirby Pkwy",
        "contact_name": "Paul Volpe",
        "contact_title": "CFO, Carlisle Corp",
        "corporate_address": None,
        "past_due_balance": 2319.77,
        "weekly_rate": 44.10,
        "status": "not started",
    },
    {
        "entity_name": "Dollar General",
        "property_address": "6659 Quince Rd",
        "contact_name": "Matthew Simonsen",
        "contact_title": "SVP",
        "corporate_address": "100 Mission Ridge, Goodlettsville, TN 37072",
        "past_due_balance": 0,
        "weekly_rate": 0,
        "status": "not started",
    },
    {
        "entity_name": "Dunkin",
        "property_address": "6331 Quince Rd",
        "contact_name": "Peter Garner",
        "contact_title": "JP Foods LLC",
        "corporate_address": "999 S Shady Grove Rd, Memphis, TN 38120",
        "past_due_balance": 0,
        "weekly_rate": 0,
        "status": "not started",
    },
]


def get_db():
    """Open (and optionally initialize) the database."""
    fresh = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    if fresh:
        for row in SEED_DATA:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?"] * len(row))
            conn.execute(
                f"INSERT INTO targets ({cols}) VALUES ({placeholders})",
                list(row.values()),
            )
        conn.commit()
    return conn


# ── Display helpers ──────────────────────────────────────────────────────────


def fmt_money(val):
    if val is None or val == 0:
        return "—"
    return f"${val:,.2f}"


def truncate(text, width):
    if text is None:
        return "—"
    text = str(text)
    return text if len(text) <= width else text[: width - 1] + "…"


def print_table(rows):
    """Print a compact summary table to stdout."""
    if not rows:
        print("  No targets found.")
        return

    # Column definitions: (header, key/formatter, width)
    header = (
        f"{'ID':>3}  {'Entity':<16} {'Address':<20} {'Past Due':>12} "
        f"{'$/Week':>10} {'Status':<17} {'Mail Track#':<24} {'Packet Sent':<12}"
    )
    sep = "─" * len(header)
    print(sep)
    print(header)
    print(sep)
    for r in rows:
        line = (
            f"{r['id']:>3}  {truncate(r['entity_name'], 16):<16} "
            f"{truncate(r['property_address'], 20):<20} "
            f"{fmt_money(r['past_due_balance']):>12} "
            f"{fmt_money(r['weekly_rate']):>10} "
            f"{truncate(r['status'], 17):<17} "
            f"{truncate(r['certified_mail_tracking'], 24):<24} "
            f"{truncate(r['date_packet_sent'], 12):<12}"
        )
        print(line)
    print(sep)
    totals = sum(r["past_due_balance"] or 0 for r in rows)
    weekly = sum(r["weekly_rate"] or 0 for r in rows)
    print(f"     {'TOTALS':<16} {'':<20} {fmt_money(totals):>12} {fmt_money(weekly):>10}")
    print()


def print_detail(r):
    """Print every field for a single target."""
    labels = [
        ("ID", r["id"]),
        ("Entity", r["entity_name"]),
        ("Property Address", r["property_address"]),
        ("Contact Name", r["contact_name"]),
        ("Contact Title", r["contact_title"]),
        ("Corporate Address", r["corporate_address"]),
        ("Past Due Balance", fmt_money(r["past_due_balance"])),
        ("Weekly Rate", fmt_money(r["weekly_rate"])),
        ("Certified Mail #", r["certified_mail_tracking"]),
        ("Date Packet Sent", r["date_packet_sent"]),
        ("Response Deadline", r["response_deadline"]),
        ("Lien Filing Date", r["lien_filing_date"]),
        ("Attorney Assigned", r["attorney_assigned"]),
        ("Status", r["status"]),
        ("Notes", r["notes"]),
    ]
    width = max(len(l) for l, _ in labels)
    print()
    for label, val in labels:
        print(f"  {label:>{width}} : {val if val is not None else '—'}")
    print()


# ── Commands ─────────────────────────────────────────────────────────────────


def cmd_list(conn, _args):
    rows = conn.execute("SELECT * FROM targets ORDER BY id").fetchall()
    print(f"\n  KIRBY GATE — Covenant Enforcement Tracker  ({len(rows)} targets)\n")
    print_table(rows)


def cmd_view(conn, args):
    row = conn.execute("SELECT * FROM targets WHERE id = ?", (args.id,)).fetchone()
    if not row:
        print(f"  Error: no target with ID {args.id}")
        return
    print_detail(row)


def cmd_update(conn, args):
    field = args.field
    value = args.value

    if field not in FIELD_NAMES:
        print(f"  Error: unknown field '{field}'")
        print(f"  Run 'python tracker.py fields' to see valid field names.")
        return

    # Validate status values
    if field == "status" and value not in VALID_STATUSES:
        print(f"  Error: invalid status '{value}'")
        print(f"  Valid statuses: {', '.join(VALID_STATUSES)}")
        return

    # Coerce numeric fields
    if field in ("past_due_balance", "weekly_rate"):
        value = value.replace("$", "").replace(",", "")
        try:
            value = float(value)
        except ValueError:
            print(f"  Error: '{args.value}' is not a valid number.")
            return

    cur = conn.execute(
        f"UPDATE targets SET {field} = ? WHERE id = ?", (value, args.id)
    )
    conn.commit()
    if cur.rowcount == 0:
        print(f"  Error: no target with ID {args.id}")
    else:
        row = conn.execute("SELECT * FROM targets WHERE id = ?", (args.id,)).fetchone()
        print(f"  Updated {row['entity_name']} — {field} = {value}")


def cmd_export(conn, args):
    filename = args.filename or f"kirby_gate_{datetime.now():%Y%m%d_%H%M%S}.csv"
    rows = conn.execute("SELECT * FROM targets ORDER BY id").fetchall()
    if not rows:
        print("  No data to export.")
        return
    keys = rows[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))
    print(f"  Exported {len(rows)} records to {os.path.abspath(filename)}")


def cmd_fields(_conn, _args):
    print("\n  Updatable fields:")
    print("  " + "─" * 40)
    for f in FIELD_NAMES:
        print(f"    {f}")
    print()
    print("  Valid statuses:")
    for s in VALID_STATUSES:
        print(f"    • {s}")
    print()


def cmd_help(_conn, _args):
    print(textwrap.dedent(__doc__))


# ── CLI wiring ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Kirby Gate — Covenant Enforcement Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="Show all targets as a table")

    p_view = sub.add_parser("view", help="Show full detail for one target")
    p_view.add_argument("id", type=int)

    p_upd = sub.add_parser("update", help="Update a field on a target")
    p_upd.add_argument("id", type=int, help="Target ID")
    p_upd.add_argument("field", help="Field name (run 'fields' to list)")
    p_upd.add_argument("value", help="New value")

    p_exp = sub.add_parser("export", help="Export all data to CSV")
    p_exp.add_argument("filename", nargs="?", help="Output filename (optional)")

    sub.add_parser("fields", help="List valid field names and statuses")
    sub.add_parser("help", help="Show usage help")

    args = parser.parse_args()
    if not args.command:
        args.command = "list"

    dispatch = {
        "list": cmd_list,
        "view": cmd_view,
        "update": cmd_update,
        "export": cmd_export,
        "fields": cmd_fields,
        "help": cmd_help,
    }

    conn = get_db()
    try:
        dispatch[args.command](conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
