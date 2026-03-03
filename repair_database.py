#!/usr/bin/env python3
"""
Database Repair Script — Cleans orphaned seances
Run this ONCE to remove sessions that reference non-existent groups/rooms/teachers.
After running, regenerate the schedule from the Admin panel.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "emploi_du_temps.db")

def repair():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    c = conn.cursor()

    # Count before
    c.execute("SELECT COUNT(*) FROM seances")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM seances WHERE salle_id NOT IN (SELECT id FROM salles)")
    bad_salle = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM seances WHERE enseignant_id NOT IN (SELECT id FROM utilisateurs)")
    bad_ens = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM seances WHERE groupe_id NOT IN (SELECT id FROM groupes)")
    bad_grp = c.fetchone()[0]

    print(f"Total seances: {total}")
    print(f"  Orphaned salle_id:      {bad_salle}")
    print(f"  Orphaned enseignant_id: {bad_ens}")
    print(f"  Orphaned groupe_id:     {bad_grp}")

    # Delete orphans (any seance where ANY FK is broken)
    c.execute("""
        DELETE FROM seances
        WHERE salle_id NOT IN (SELECT id FROM salles)
           OR enseignant_id NOT IN (SELECT id FROM utilisateurs)
           OR groupe_id NOT IN (SELECT id FROM groupes)
    """)
    deleted = c.rowcount
    conn.commit()

    # Count after
    c.execute("SELECT COUNT(*) FROM seances")
    remaining = c.fetchone()[0]

    print(f"\n✅ Deleted {deleted} orphaned seances")
    print(f"   Remaining valid seances: {remaining}")
    conn.close()

if __name__ == "__main__":
    repair()
