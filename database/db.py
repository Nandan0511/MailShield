# 🗄️ database/db.py

import sqlite3

from pathlib import Path


# ---------------------------------------------------
# DATABASE PATH
# ---------------------------------------------------
DB_PATH = Path("database/mailshield.db")


# ---------------------------------------------------
# CREATE CONNECTION
# ---------------------------------------------------
def get_connection():

    conn = sqlite3.connect(

        DB_PATH,

        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    # -----------------------------------------------
    # ENABLE WAL MODE
    # -----------------------------------------------
    conn.execute(
        "PRAGMA journal_mode=WAL;"
    )

    return conn


# ---------------------------------------------------
# MIGRATE: gmail_message_id UNIQUE -> (gmail_message_id, account_email) UNIQUE
# ---------------------------------------------------
def _migrate_message_id_uniqueness(conn):

    # Original schema made gmail_message_id globally UNIQUE.
    # Gmail message IDs are only guaranteed unique *within*
    # a single account/mailbox — with multi-account support,
    # two accounts' message IDs can collide, silently
    # dropping the second account's email via INSERT OR
    # IGNORE. This rebuilds the table with a composite
    # UNIQUE(gmail_message_id, account_email) constraint,
    # preserving all existing data.

    cursor = conn.cursor()

    cursor.execute("PRAGMA index_list(email_scans)")

    indexes = cursor.fetchall()

    # The constraint we want in place: a unique index (in
    # either column order) covering exactly these two columns.
    target_cols = {"gmail_message_id", "account_email"}

    has_correct_constraint = False

    for idx in indexes:

        if not idx["unique"]:
            continue

        cursor.execute(f"PRAGMA index_info({idx['name']})")

        cols = {row["name"] for row in cursor.fetchall()}

        if cols == target_cols:

            has_correct_constraint = True

            break

    # Migrate whenever the composite constraint is missing —
    # this covers both the original single-column
    # UNIQUE(gmail_message_id) schema *and* databases that
    # somehow ended up with no uniqueness constraint on these
    # columns at all (observed in practice: a live DB with 400
    # rows had zero unique indexes on gmail_message_id).
    if has_correct_constraint:
        return

    cursor.execute("ALTER TABLE email_scans RENAME TO email_scans_old")

    cursor.execute(
        """
        CREATE TABLE email_scans (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            gmail_message_id TEXT,

            account_email TEXT,

            subject TEXT,

            sender TEXT,

            recipient TEXT,

            prediction TEXT,

            confidence REAL,

            email_time TEXT,

            scan_time TEXT,

            content TEXT,

            UNIQUE(gmail_message_id, account_email)
        )
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO email_scans (
            id, gmail_message_id, account_email, subject,
            sender, recipient, prediction, confidence,
            email_time, scan_time, content
        )
        SELECT
            id, gmail_message_id, account_email, subject,
            sender, recipient, prediction, confidence,
            email_time, scan_time, content
        FROM email_scans_old
        """
    )

    cursor.execute("DROP TABLE email_scans_old")

    conn.commit()


# ---------------------------------------------------
# INITIALIZE DATABASE
# ---------------------------------------------------
def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    # -----------------------------------------------
    # EMAIL SCANS TABLE
    # -----------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS email_scans (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            gmail_message_id TEXT,

            account_email TEXT,

            subject TEXT,

            sender TEXT,

            recipient TEXT,

            prediction TEXT,

            confidence REAL,

            email_time TEXT,

            scan_time TEXT,

            content TEXT,

            UNIQUE(gmail_message_id, account_email)
        )
        """
    )

    # -----------------------------------------------
    # MIGRATE EXISTING DB IF IT HAS THE OLD CONSTRAINT
    # -----------------------------------------------
    _migrate_message_id_uniqueness(conn)

    # -----------------------------------------------
    # CREATE INDEXES
    # -----------------------------------------------
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_account
        ON email_scans(account_email)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prediction
        ON email_scans(prediction)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scan_time
        ON email_scans(scan_time)
        """
    )

    # ---------------------------------------------------
    # SCAN STATE TABLE
    # ---------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_state (

        account_email TEXT PRIMARY KEY,

        last_message_id TEXT)
    """
    )

    conn.commit()

    conn.close()
