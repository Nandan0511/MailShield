# 📩 utils/email_utils.py

import base64

from bs4 import BeautifulSoup
from datetime import datetime


# ---------------------------------------------------
# EXTRACT LINKS FROM HTML
# ---------------------------------------------------
def _extract_links(soup):

    # ------------------------------------------------
    # Pull real destination URLs out of anchor tags.
    # Visible link text (e.g. "Click here") hides the
    # actual href from plain-text extraction, which is
    # exactly what phishing emails rely on — cloaking a
    # malicious URL behind innocuous text. Without this,
    # detect_phishing() never sees the real link.
    # ------------------------------------------------
    links = []

    for tag in soup.find_all("a", href=True):

        href = tag["href"].strip()

        if href and href not in links:

            links.append(href)

    return links


# ---------------------------------------------------
# EXTRACT EMAIL CONTENT
# ---------------------------------------------------
def extract_email_content(payload):

    if "parts" in payload:

        # ------------------------------------------------
        # Prefer text/html over text/plain when both exist,
        # since the HTML part carries the real hrefs needed
        # for phishing/link analysis. Fall back to whatever
        # part yields content otherwise.
        # ------------------------------------------------
        html_result = None
        first_result = None

        for part in payload["parts"]:

            result = extract_email_content(part)

            if result and first_result is None:

                first_result = result

            if result and part.get("mimeType") == "text/html":

                html_result = result

        return html_result or first_result

    else:

        data = payload["body"].get("data")

        mime = payload.get("mimeType")

        if data:

            try:

                decoded = (
                    base64.urlsafe_b64decode(data)
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

                if mime == "text/html":

                    soup = BeautifulSoup(
                        decoded,
                        "html.parser"
                    )

                    text = soup.get_text()

                    links = _extract_links(soup)

                    # ---------------------------------
                    # Append extracted links so they are
                    # visible to phishing/keyword analysis
                    # (which only scans the returned text).
                    # ---------------------------------
                    if links:

                        text += (
                            "\n\n[LINKS]: "
                            + " ".join(links)
                        )

                    return text

                return decoded

            except Exception:

                return "(Error decoding content)"

    return None

# ---------------------------------------------------
# SINGLE EMAIL FETCH
# ---------------------------------------------------
def get_email_content(
    service,
    msg_id
):

    msg = (
        service.users().messages().get(

            userId="me",

            id=msg_id,

            format="full"

        ).execute()
    )

    headers = msg["payload"].get(
        "headers",
        []
    )

    subject = next(
        (
            h["value"]

            for h in headers

            if h["name"] == "Subject"
        ),
        "(No Subject)"
    )

    sender = next(
        (
            h["value"]

            for h in headers

            if h["name"] == "From"
        ),
        "(Unknown Sender)"
    )

    recipient = next(
        (
            h["value"]

            for h in headers

            if h["name"] == "To"
        ),
        "(Unknown Recipient)"
    )

    timestamp = int(
        msg.get(
            "internalDate",
            0
        )
    ) // 1000

    time_str = datetime.fromtimestamp(
        timestamp
    ).strftime(
        "%Y-%m-%d %I:%M %p"
    )

    content = extract_email_content(
        msg["payload"]
    ) or "(No content)"

    return (
        subject,
        sender,
        recipient,
        time_str,
        content
    )
# ---------------------------------------------------
# BATCH FETCH EMAILS (SAFE FOR >100 EMAILS)
# ---------------------------------------------------
def batch_get_email_contents(
    service,
    message_ids
):

    emails = []

    def callback(
        request_id,
        response,
        exception
    ):

        if exception:

            emails.append({
                "id": request_id,
                "error": str(exception)
            })

            return

        try:

            headers = response["payload"].get(
                "headers",
                []
            )

            subject = next(
                (
                    h["value"]
                    for h in headers
                    if h["name"] == "Subject"
                ),
                "(No Subject)"
            )

            sender = next(
                (
                    h["value"]
                    for h in headers
                    if h["name"] == "From"
                ),
                "(Unknown Sender)"
            )

            recipient = next(
                (
                    h["value"]
                    for h in headers
                    if h["name"] == "To"
                ),
                "(Unknown Recipient)"
            )

            timestamp = int(
                response.get(
                    "internalDate",
                    0
                )
            ) // 1000

            time_str = datetime.fromtimestamp(
                timestamp
            ).strftime(
                "%Y-%m-%d %I:%M %p"
            )

            content = extract_email_content(
                response["payload"]
            ) or "(No content)"

            emails.append({

                "id": request_id,

                "subject": subject,

                "sender": sender,

                "recipient": recipient,

                "time": time_str,

                "content": content
            })

        except Exception as e:

            emails.append({

                "id": request_id,

                "error": str(e)
            })

    # -----------------------------------------------
    # GMAIL LIMIT = 100 REQUESTS PER BATCH
    # -----------------------------------------------
    BATCH_SIZE = 20

    for start in range(
        0,
        len(message_ids),
        BATCH_SIZE
    ):

        chunk = message_ids[
            start:start + BATCH_SIZE
        ]

        batch = service.new_batch_http_request()

        for msg_id in chunk:

            batch.add(

                service.users().messages().get(

                    userId="me",

                    id=msg_id,

                    format="full"

                ),

                callback=callback,

                request_id=msg_id
            )

        batch.execute()

    return emails

# ---------------------------------------------------
# LABEL HANDLING
# ---------------------------------------------------
def get_or_create_label(
    service,
    label_name
):

    labels = (
        service.users().labels().list(
            userId="me"
        ).execute().get(
            "labels",
            []
        )
    )

    for label in labels:

        if label["name"] == label_name:

            return label["id"]

    label_obj = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show"
    }

    label = (
        service.users().labels().create(
            userId="me",
            body=label_obj
        ).execute()
    )

    return label["id"]
