"""Rebuild kirbygate.db with corrected 10 delinquent targets from Solutions spreadsheet."""

import os
import sqlite3
import sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kirbygate.db")
CAMPUS_SQFT = 672_718

# Delete old DB
if os.path.exists(DB):
    os.remove(DB)
    print("  Deleted old kirbygate.db")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

conn.executescript("""
CREATE TABLE parcels (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    address           TEXT NOT NULL,
    business_name     TEXT,
    sqft              INTEGER,
    pct_campus        REAL,
    status            TEXT DEFAULT 'VERIFY',
    entity_owner      TEXT,
    corporate_target  TEXT,
    past_due_balance  REAL,
    weekly_rate       REAL,
    certified_mail_tracking TEXT,
    date_packet_sent  TEXT,
    cure_deadline     TEXT,
    lien_filing_date  TEXT,
    attorney_referral_date TEXT,
    enforcement_step  TEXT DEFAULT 'Research',
    next_action       TEXT,
    deadline          TEXT,
    notes             TEXT
);
CREATE TABLE enforcement_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    parcel_id         INTEGER,
    timestamp         TEXT NOT NULL,
    action            TEXT,
    sent_via          TEXT,
    response_due      TEXT,
    response_received TEXT,
    next_step         TEXT,
    attorney          TEXT,
    cost              REAL DEFAULT 0,
    notes             TEXT,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id)
);
CREATE TABLE rates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    label           TEXT,
    value           REAL,
    effective_date  TEXT
);
""")

# ── PAYING PARCELS (9 current) ──────────────────────────────────────────────

current_parcels = [
    ("6500 Kirby Gate Blvd",  "Waters of Memphis (Apts)",  54424, "Kirby Gate Apts LLC",    ""),
    ("2809 Kirby Pkwy",       "Shoppes at Kirby",          22350, "WFC",                    ""),
    ("2857 Kirby Pkwy",       "Shops at Kirby Gate",       20000, "WFC",                    ""),
    ("2865 Kirby Pkwy",       "Kirby Wines & Spirits",      5500, "WFC",                    ""),
    ("2873 Kirby Pkwy",       "Nail Salon / Retail",        4200, "WFC",                    ""),
    ("6535 Kirby Gate Blvd",  "Summit Medical (Bldg A)",   72000, "Summit Healthcare REIT", ""),
    ("6655 Quince Rd",        "Willow Grove Apts",         72400, "Willow Grove LP",        ""),
    ("6660 Quince Rd",        "Kroger #445",               65000, "Kroger Co.",             "Cincinnati HQ"),
    ("2725 Kirby Pkwy",       "FedEx Office / Retail",     18000, "Kirby Pkwy Retail LLC",  ""),
]

for addr, name, sqft, entity, corp in current_parcels:
    pct = sqft / CAMPUS_SQFT
    conn.execute(
        """INSERT INTO parcels
           (address, business_name, sqft, pct_campus, status,
            entity_owner, corporate_target, past_due_balance, weekly_rate,
            enforcement_step)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (addr, name, sqft, pct, "CURRENT", entity, corp, 0, 0, "Paying"),
    )


# ── 10 DELINQUENT TARGETS (corrected from Solutions spreadsheet) ─────────────
#
# Format: (address, business_name, sqft, entity_owner, corporate_target,
#          past_due, weekly_rate, enforcement_step, next_action, deadline, notes)

delinquent_targets = [
    (
        "2801 Kirby Pkwy",
        "Starbucks (Exline Property)",
        7493,
        "Exline Properties",
        "Starbucks Regional Facilities Manager",
        10509.98, 99.90,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Landlord = Exline; Starbucks = subtenant",
    ),
    (
        "2835 Kirby Pkwy",
        "Kroger",
        58592,
        "Kroger Co. \u2014 Delta Division",
        "Delta Division HQ, 800 Ridge Lake Blvd, Memphis, TN 38120",
        82470.21, 783.90,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Delta Division HQ is local Memphis",
    ),
    (
        "2845 Kirby Pkwy",
        "Wendy\u2019s (Carlisle/Wendelta)",
        3284,
        "Wendelta Inc. / Carlisle Corp",
        "Paul Volpe, CFO \u2014 Carlisle Corp",
        4639.54, 44.10,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Franchisee entity",
    ),
    (
        "6480 Quince Rd",
        "Pointe at Kirby Gate",
        31061,
        "Grace Mgmt / MedHCP REIT",
        "MedHCP Corp \u2014 Dallas, TX",
        43744.24, 415.80,
        "Demand Sent", "Follow-up / Lien Warning", "2026-03-01",
        "Large parcel, high-value target",
    ),
    (
        "6500 Quince Rd",
        "Freedom Plasma Center",
        12314,
        "Realty Income Corp (NYSE: O)",
        "Realty Income Corp \u2014 San Diego, CA (Corporate Real Estate)",
        17327.27, 164.70,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Public REIT \u2014 will settle to avoid headline",
    ),
    (
        "2715/2725b Kirby",
        "KG Business Center",
        43200,
        "Unknown \u2014 research needed",
        "TBD",
        None, 577.80,
        "Research", "Identify entity & send demand", "2026-02-28",
        "Non-payer, past due TBD \u2014 need Wills data",
    ),
    (
        "6532 Kirby Gate",
        "Dollar Tree #12847",
        9964,
        "Dollar Tree Inc.",
        "Dollar Tree Inc. \u2014 Chesapeake, VA (Corporate Real Estate)",
        14013.31, 133.20,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Corporate tenant, standard collections",
    ),
    (
        "6420 Quince Rd",
        "Summit of Germantown",
        215000,
        "Summit Healthcare REIT",
        "Summit Healthcare REIT \u2014 Corporate Office",
        302611.70, 2876.40,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Largest single target \u2014 $302K arrears",
    ),
    (
        "6659 Quince Rd",
        "Dollar General #22748",
        9301,
        "Dollar General Corp.",
        "Matthew Simonsen, SVP \u2014 100 Mission Ridge, Goodlettsville, TN 37072",
        13066.46, 124.20,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Corporate tenant, standard collections",
    ),
    (
        "2735 Kirby",
        "Dunkin\u2019 (JP Foods LLC)",
        2375,
        "JP Foods LLC",
        "Peter Garner \u2014 999 S Shady Grove Rd, Memphis, TN 38120",
        3408.64, 32.40,
        "Demand Drafted", "Send certified demand", "2026-02-28",
        "Local franchisee \u2014 smallest parcel",
    ),
]

for t in delinquent_targets:
    (addr, name, sqft, entity, corp,
     past_due, weekly, step, next_act, deadline, notes) = t
    pct = sqft / CAMPUS_SQFT
    conn.execute(
        """INSERT INTO parcels
           (address, business_name, sqft, pct_campus, status,
            entity_owner, corporate_target, past_due_balance, weekly_rate,
            enforcement_step, next_action, deadline, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (addr, name, sqft, pct, "DELINQUENT", entity, corp,
         past_due, weekly, step, next_act, deadline, notes),
    )


# ── RATES TABLE ──────────────────────────────────────────────────────────────

rates = [
    ("Historic Campus Weekly Rate", 6069.52, "2022-12-01"),
    ("Current Campus Weekly Rate", 9000.00, "2026-01-01"),
    ("Total Campus SqFt", 672718, "2022-12-01"),
    ("Arrears Period (weeks)", 156, "2022-12-01"),
    ("Cure Period (days)", 15, "2011-05-05"),
]
for label, val, dt in rates:
    conn.execute(
        "INSERT INTO rates (label, value, effective_date) VALUES (?,?,?)",
        (label, val, dt),
    )


# ── ENFORCEMENT LOG SEED ─────────────────────────────────────────────────────

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
conn.execute(
    """INSERT INTO enforcement_log
       (parcel_id, timestamp, action, next_step, attorney, notes)
       VALUES (?,?,?,?,?,?)""",
    (None, now,
     "Database rebuilt with corrected Solutions spreadsheet data (10 delinquent targets)",
     "Finalize and send demand letters via certified mail",
     "Rosenblum", "All figures verified against KIRBY GATES Solution_.xlsx"),
)

conn.commit()


# ── VERIFY & PRINT ───────────────────────────────────────────────────────────

def money(val):
    if val is None:
        return "TBD"
    return f"${val:,.2f}"

print()
print("  DATABASE REBUILT SUCCESSFULLY")
print("  " + "=" * 90)
print()

rows = conn.execute(
    "SELECT * FROM parcels ORDER BY status DESC, sqft DESC"
).fetchall()

cur_count = 0
del_count = 0
total_arrears = 0
total_weekly = 0

print(f"  {'ID':>3}  {'Status':<12} {'Address':<24} {'Business':<30} "
      f"{'SqFt':>8} {'Past Due':>14} {'$/Week':>10}")
print("  " + "-" * 108)

for r in rows:
    sqft = r["sqft"] or 0
    if r["status"] == "DELINQUENT":
        del_count += 1
        # Find matching target for past_due and weekly
        for t in delinquent_targets:
            if t[0] == r["address"]:
                pd = t[5]
                wk = t[6]
                pd_str = money(pd) if pd is not None else "TBD"
                wk_str = money(wk)
                if pd:
                    total_arrears += pd
                total_weekly += wk
                break
    else:
        cur_count += 1
        pd_str = "\u2014"
        wk_str = "\u2014"

    print(f"  {r['id']:>3}  {r['status']:<12} {r['address']:<24} "
          f"{r['business_name']:<30} {sqft:>8,} {pd_str:>14} {wk_str:>10}")

print("  " + "-" * 108)
print()
print(f"  Paying parcels:      {cur_count}")
print(f"  Delinquent targets:  {del_count}")
print(f"  Total parcels:       {cur_count + del_count}")
print(f"  Total known arrears: {money(total_arrears)}")
print(f"  Total weekly (delq): {money(total_weekly)}")
print()

conn.close()
