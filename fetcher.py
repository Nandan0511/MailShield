# fetcher.py

import time
import socket
import streamlit as st

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from email.utils import getaddresses

from googleapiclient.errors import HttpError

from classifier import classify_message

from database.queries import (
    save_email_scan,
    get_last_message_id,
    update_last_message_id,
    get_existing_message_ids,
    save_email_scans_batch,
)

from utils.session import (
    initialize_session_state
)

from utils.email_utils import (
    batch_get_email_contents,
    get_or_create_label
)

from security.phishing_detector import (
    detect_phishing
)

from utils.logger import (
    log_info,
    log_error
)

initialize_session_state()


# ---------------------------------------------------
# SAFE API RETRY
# ---------------------------------------------------
def safe_api_call(
    callable_func,
    retries=3,
    delay=1
):
    for attempt in range(retries):

        try:
            return callable_func()

        except (
            HttpError,
            socket.error,
            ConnectionResetError,
            TimeoutError
        ) as e:

            if attempt < retries - 1:

                wait = delay * (2 ** attempt)

                time.sleep(wait)

            else:
                raise e


# ---------------------------------------------------
# FETCH MESSAGE IDS
# ---------------------------------------------------
def fetch_message_ids(
    service,
    query,
    limit
):
    messages = []

    page_token = None

    while len(messages) < limit:

        response = safe_api_call(
            lambda: service.users().messages().list(
                userId="me",
                q=query,
                maxResults=min(
                    100,
                    limit - len(messages)
                ),
                pageToken=page_token
            ).execute()
        )

        batch = response.get(
            "messages",
            []
        )

        messages.extend(batch)

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return messages[:limit]


# ---------------------------------------------------
# CLASSIFY EMAIL
# ---------------------------------------------------
def classify_single_email(
    email,
    model,
    vectorizer
):
    try:

        prediction, confidence = classify_message(
            email.get("content", ""),
            model,
            vectorizer
        )

        email["prediction"] = prediction
        email["confidence"] = confidence

        return email

    except Exception as e:

        email["prediction"] = "UNKNOWN"
        email["confidence"] = 0
        email["classification_error"] = str(e)

        return email


# ---------------------------------------------------
# MAIN FETCH FUNCTION
# ---------------------------------------------------
def fetch_and_classify_emails(
    service,
    model,
    vectorizer,
    days=7,
    limit=50,
    label_emails=True
):

    account_email = st.session_state.get(
        "email",
        "unknown"
    )

    # -----------------------------------------------
    # SETTINGS
    # -----------------------------------------------
    days = st.session_state.get(
        "scan_days",
        days
    )

    requested_limit = st.session_state.get(
        "email_limit",
        limit
    )

    label_emails = st.session_state.get(
        "label_emails",
        label_emails
    )

    # -----------------------------------------------
    # DATABASE STATE
    # -----------------------------------------------
    existing_ids = get_existing_message_ids(
        account_email
    )

    from database.queries import (
    get_email_count_for_days
    )

    current_count = (
    get_email_count_for_days(
        account_email,
        days
     )
    )

    last_id = get_last_message_id(
        account_email
    )

    # -----------------------------------------------
    # FETCH MODE
    # -----------------------------------------------
    # "historical_fetch" means we still need to backfill
    # older emails to satisfy the requested limit/day window.
    #
    # IMPORTANT: even once the quota is satisfied, we must
    # still check the inbox for messages newer than
    # `last_id` — otherwise new spam/ham arriving after the
    # quota was hit would never be scanned again. Previously
    # this function returned early here, which silently
    # stopped scanning new mail once `current_count` reached
    # `requested_limit`.
    # -----------------------------------------------
    historical_fetch = current_count < requested_limit

    if historical_fetch:

        fetch_limit = requested_limit

    else:

        log_info(
            f"Stored quota met ({current_count}/{requested_limit}) "
            f"— checking inbox for new mail only"
        )

        # Use a generous cap so a page of newest message IDs is
        # large enough to reach `last_id` (where we stop) even if
        # several new emails have arrived since the last scan.
        fetch_limit = max(requested_limit, 200)

    # -----------------------------------------------
    # GMAIL QUERY
    # -----------------------------------------------
    query = (
        f"in:inbox newer_than:{days}d"
    )

    spam_emails = []
    ham_emails = []

    sender_count = defaultdict(int)
    recipient_count = defaultdict(int)

    error_log = []

    status = st.empty()
    progress = st.progress(0)

    try:

        # -------------------------------------------
        # FETCH IDS
        # -------------------------------------------
        status.info(
            "📨 Fetching email IDs..."
        )

        messages = fetch_message_ids(
            service=service,
            query=query,
            limit=fetch_limit
        )

        if not messages:

            status.warning(
                "📭 No emails found."
            )

            return (
                [],
                [],
                {},
                {},
                []
            )

        # -------------------------------------------
        # DETERMINE WHICH EMAILS TO FETCH
        # -------------------------------------------
        message_ids = []

        for msg in messages:

            msg_id = msg.get("id")

            if msg_id in existing_ids:
                continue

            if (
                not historical_fetch
                and last_id
                and msg_id == last_id
            ):
                break

            message_ids.append(msg_id)

        if not message_ids:

            status.info(
                "📭 Inbox already up-to-date"
            )
            st.rerun()

            return None

        # -------------------------------------------
        # FETCH EMAIL CONTENTS
        # -------------------------------------------
        status.info(
            "📥 Fetching email contents..."
        )

        email_data = batch_get_email_contents(
            service,
            message_ids
        )

        email_data = [

            email

            for email in email_data

            if "error" not in email
        ]

        if not email_data:

            status.warning(
                "⚠️ No valid emails could be loaded."
            )

            return (
                [],
                [],
                {},
                {},
                []
            )

        # -------------------------------------------
        # CLASSIFICATION
        # -------------------------------------------
        status.info(
            "🧠 Classifying emails..."
        )

        with ThreadPoolExecutor(
            max_workers=4
        ) as executor:

            classified_results = list(

                executor.map(

                    lambda email:

                    classify_single_email(
                        email,
                        model,
                        vectorizer
                    ),

                    email_data
                )
            )

        # -------------------------------------------
        # LABEL IDS
        # -------------------------------------------
        spam_label_id = None
        ham_label_id = None

        if label_emails:

            spam_label_id = get_or_create_label(
            service,
            "MailShield-SPAM"
        )

            ham_label_id = get_or_create_label(
            service,
            "MailShield-HAM"
        )

        # -------------------------------------------
        # PROCESS RESULTS
        # -------------------------------------------
        status.info(
            "🏷️ Processing emails..."
        )

        total_results = len(
            classified_results
        )
        emails_to_save = []

        for index, email in enumerate(
            classified_results
        ):


            try:

                prediction = email.get(
                    "prediction",
                    "UNKNOWN"
                )

                msg_id = email.get("id")

                if (
                    "SPAM" not in prediction
                    and
                    "HAM" not in prediction
                ):
                    continue

                # -------------------------------
                # LABEL EMAIL
                # -------------------------------
                if label_emails:

                    try:

                        label_id = (

                            spam_label_id

                            if "SPAM" in prediction

                            else ham_label_id
                        )

                        safe_api_call(
                            lambda:
                            service.users()
                            .messages()
                            .modify(
                                userId="me",
                                id=msg_id,
                                body={
                                    "addLabelIds": [
                                        label_id
                                    ]
                                }
                            )
                            .execute()
                        )

                    except Exception as e:

                        error_log.append({

                            "message_id":
                            msg_id,

                            "error":
                            str(e)
                        })

                # -------------------------------
                # PHISHING ANALYSIS
                # -------------------------------
                phishing_result = detect_phishing(
                    email.get(
                        "content",
                        ""
                    )
                )

                email_info = {

                    "id":
                    msg_id,

                    "subject":
                    email.get(
                        "subject",
                        "(No Subject)"
                    ),

                    "sender":
                    email.get(
                        "sender",
                        "(Unknown Sender)"
                    ),

                    "recipient":
                    email.get(
                        "recipient",
                        "(Unknown Recipient)"
                    ),

                    "time":
                    email.get(
                        "time",
                        ""
                    ),

                    "content":
                    email.get(
                        "content",
                        ""
                    ),

                    "prediction":
                    prediction,

                    "confidence":
                    email.get(
                        "confidence",
                        0
                    ),

                    "risk":
                    phishing_result["risk"],

                    "risk_score":
                    phishing_result["score"],

                    "phishing_reasons":
                    ", ".join(
                        phishing_result[
                            "reasons"
                        ]
                    ),

                    "is_new":
                    msg_id not in existing_ids
                }

                # -------------------------------
                # COUNTS
                # -------------------------------
                sender_count[
                    email_info["sender"]
                ] += 1

                for _, addr in getaddresses(
                    [email_info["recipient"]]
                ):

                    if addr:

                        recipient_count[
                            addr
                        ] += 1

                # -------------------------------
                # ADD TO BATCH SAVE LIST
                # -------------------------------
                emails_to_save.append(
                  email_info
                )

                existing_ids.add(
                 msg_id
               )

                # -------------------------------
                # STORE
                # -------------------------------
                if "SPAM" in prediction:

                    spam_emails.append(
                        email_info
                    )

                else:

                    ham_emails.append(
                        email_info
                    )

                progress.progress(
                    (index + 1)
                    / total_results
                )

            except Exception as e:

                error_log.append({

                    "message_id":
                    email.get(
                        "id",
                        "UNKNOWN"
                    ),

                    "error":
                    str(e)
                })

        # -------------------------------------------
        # SAVE ALL EMAILS IN ONE DB COMMIT
        # -------------------------------------------
        if emails_to_save:

            save_email_scans_batch(
               emails_to_save,
                account_email
    )

        # -------------------------------------------
        # SAVE LAST SCANNED ID
        # -------------------------------------------
        if messages:

            update_last_message_id(
                account_email,
                messages[0]["id"]
            )

        # -------------------------------------------
        # LOGGING
        # -------------------------------------------
        log_info(
            f"Scan Complete | "
            f"HAM: {len(ham_emails)} | "
            f"SPAM: {len(spam_emails)}"
        )

        return (
            spam_emails,
            ham_emails,
            sender_count,
            recipient_count,
            error_log
        )

    finally:

        progress.empty()

        try:
            status.empty()
        except Exception:
            pass