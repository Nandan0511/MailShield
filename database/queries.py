# 📊 database/queries.py

from datetime import datetime

from database.db import (
    get_connection
)
from dateutil import parser
from datetime import datetime, timedelta

# ---------------------------------------------------
# SAVE EMAIL SCAN
# ---------------------------------------------------
def save_email_scan(
    email_data,
    account_email
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO email_scans (

            gmail_message_id,

            account_email,

            subject,

            sender,

            recipient,

            prediction,

            confidence,

            email_time,

            scan_time,

            content

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (

            email_data.get("id"),

            account_email,

            email_data.get("subject"),

            email_data.get("sender"),

            email_data.get("recipient"),

            email_data.get("prediction"),

            email_data.get("confidence"),

            email_data.get("time"),

            datetime.now().strftime(
                "%Y-%m-%d %I:%M %p"
            ),

            email_data.get("content")
        )
    )

    conn.commit()

    conn.close()


# ---------------------------------------------------
# GET ALL EXISTING MESSAGE IDS (FAST)
# ---------------------------------------------------
def get_existing_message_ids(account_email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT gmail_message_id
        FROM email_scans
        WHERE account_email = ?
        """,
        (account_email,)
    )

    rows = cursor.fetchall()
    conn.close()

    return set(row["gmail_message_id"] for row in rows)

# ---------------------------------------------------
# FETCH RECENT SCANS
# ---------------------------------------------------
def get_recent_scans(
    account_email,
    limit=100
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *

        FROM email_scans

        WHERE account_email = ?

        ORDER BY id DESC

        LIMIT ?
        """,

        (
            account_email,
            limit
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [

        dict(row)

        for row in rows
    ]


# ---------------------------------------------------
# FETCH ACCOUNT STATS
# ---------------------------------------------------
def get_account_stats(
    account_email
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            account_email,

            prediction,

            COUNT(*) as total

        FROM email_scans

        WHERE account_email = ?

        GROUP BY
            account_email,
            prediction
        """,

        (account_email,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [

        dict(row)

        for row in rows
    ]


# ---------------------------------------------------
# FETCH SPAM TREND
# ---------------------------------------------------
def get_spam_trend(
    account_email
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            scan_time,

            COUNT(*) as spam_count

        FROM email_scans

        WHERE

            prediction = '🚫 SPAM'

            AND account_email = ?

        GROUP BY scan_time

        ORDER BY scan_time ASC
        """,

        (account_email,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [

        dict(row)

        for row in rows
    ]


# ---------------------------------------------------
# SEARCH EMAILS
# ---------------------------------------------------
def search_emails(
    keyword,
    account_email
):

    conn = get_connection()

    cursor = conn.cursor()

    query = f"%{keyword}%"

    cursor.execute(
        """
        SELECT *

        FROM email_scans

        WHERE

            account_email = ?

            AND (

                subject LIKE ?

                OR sender LIKE ?

                OR recipient LIKE ?

                OR prediction LIKE ?
            )

        ORDER BY id DESC
        """,

        (
            account_email,
            query,
            query,
            query,
            query
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [

        dict(row)

        for row in rows
    ]

# ---------------------------------------------------
# GET LAST SCANNED MESSAGE ID
# ---------------------------------------------------
def get_last_message_id(account_email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT last_message_id
        FROM scan_state
        WHERE account_email = ?
        """,
        (account_email,)
    )

    row = cursor.fetchone()
    conn.close()

    return row["last_message_id"] if row else None


# ---------------------------------------------------
# UPDATE LAST SCANNED MESSAGE ID
# ---------------------------------------------------
def update_last_message_id(account_email, message_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO scan_state (account_email, last_message_id)
        VALUES (?, ?)
        ON CONFLICT(account_email)
        DO UPDATE SET last_message_id = excluded.last_message_id
        """,
        (account_email, message_id)
    )

    conn.commit()
    conn.close()

# ---------------------------------------------------
# COUNT EMAILS IN DB
# ---------------------------------------------------
def get_email_count(account_email):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM email_scans
        WHERE account_email = ?
        """,
        (account_email,)
    )

    row = cursor.fetchone()

    conn.close()

    return row["total"] if row else 0

def load_emails_from_db(account_email, limit=50, days=7):

    from dateutil import parser
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------
    # PUSH THE DATE CUTOFF INTO SQL
    # -----------------------------------------------
    # email_time is always stored as "%Y-%m-%d %I:%M %p"
    # (zero-padded 12-hour clock + AM/PM), which happens to
    # sort correctly as a plain string ("AM" < "PM", and
    # zero-padded hours/minutes compare the same as
    # numerically). That lets SQLite filter directly instead
    # of loading and dateutil-parsing every row in Python,
    # which got slower the larger email_scans grew.
    # -----------------------------------------------
    cutoff = (
        datetime.now() - timedelta(days=days)
    ).strftime("%Y-%m-%d %I:%M %p")

    cursor.execute(
        """
        SELECT *
        FROM email_scans
        WHERE account_email = ?
          AND email_time >= ?
        ORDER BY email_time DESC
        """,
        (account_email, cutoff)
    )

    rows = cursor.fetchall()
    conn.close()

    emails = []

    for row in rows:
        data = dict(row)

        # normalize time
        data["time"] = data.get("email_time")

        emails.append(data)

    # -----------------------------------------------
    # SAFETY NET FOR ANY MALFORMED TIME STRINGS
    # -----------------------------------------------
    # The SQL filter above assumes the standard format. If a
    # row has a malformed/legacy timestamp that didn't match
    # the string-comparable cutoff correctly, re-validate with
    # a real parse before trusting it, same as before.
    cutoff_dt = datetime.now() - timedelta(days=days)

    verified_emails = []

    for e in emails:
        try:
            email_time = parser.parse(e["time"])

            if email_time >= cutoff_dt:
                verified_emails.append(e)

        except Exception:
            continue

    # -----------------------------------------------
    # APPLY LIMIT AFTER FILTER
    # -----------------------------------------------
    filtered_emails = verified_emails[:limit]

    # -----------------------------------------------
    # SPLIT INTO SPAM / HAM
    # -----------------------------------------------
    spam = [e for e in filtered_emails if e["prediction"] == "🚫 SPAM"]
    ham = [e for e in filtered_emails if e["prediction"] == "✅ HAM"]

    return spam, ham

def get_email_count_for_days(
    account_email,
    days
):
    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------
    # SQL-SIDE CUTOFF (see load_emails_from_db for why
    # string comparison against this format is safe)
    # -----------------------------------------------
    cutoff_str = (
        datetime.now() - timedelta(days=days)
    ).strftime("%Y-%m-%d %I:%M %p")

    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM email_scans
        WHERE account_email = ?
          AND email_time >= ?
        """,
        (account_email, cutoff_str)
    )

    row = cursor.fetchone()
    conn.close()

    return row["total"] if row else 0

# ---------------------------------------------------
# SAVE EMAILS IN BATCH
# ---------------------------------------------------
def save_email_scans_batch(
    emails,
    account_email
):

    conn = get_connection()

    cursor = conn.cursor()

    rows = []

    for email_data in emails:

        rows.append(

            (

                email_data.get("id"),

                account_email,

                email_data.get("subject"),

                email_data.get("sender"),

                email_data.get("recipient"),

                email_data.get("prediction"),

                email_data.get("confidence"),

                email_data.get("time"),

                datetime.now().strftime(
                    "%Y-%m-%d %I:%M %p"
                ),

                email_data.get("content")

            )

        )

    cursor.executemany(

        """
        INSERT OR IGNORE INTO email_scans (

            gmail_message_id,

            account_email,

            subject,

            sender,

            recipient,

            prediction,

            confidence,

            email_time,

            scan_time,

            content

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        rows

    )

    conn.commit()

    conn.close()