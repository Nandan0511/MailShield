# 🗂 utils/token_utils.py

import os
import stat
import shutil


# ---------------------------------------------------
# TOKEN ROOT
# ---------------------------------------------------
TOKEN_DIR = "tokens"


# ---------------------------------------------------
# ENCODE EMAIL
# ---------------------------------------------------
def encode_email_for_path(
    email: str
) -> str:

    return (
        email
        .replace("@", "_at_")
        .replace(".", "_dot_")
    )


# ---------------------------------------------------
# DECODE EMAIL
# ---------------------------------------------------
def decode_path_to_email(
    safe_email: str
) -> str:

    if (
        "_at_" in safe_email
        and "_dot_" in safe_email
    ):

        return (
            safe_email
            .replace("_at_", "@")
            .replace("_dot_", ".")
        )

    return safe_email


# ---------------------------------------------------
# GET TOKEN PATH
# ---------------------------------------------------
# def get_token_path(
#     email: str
# ) -> str:

#     safe_email = encode_email_for_path(
#         email
#     )

#     return os.path.join(
#         TOKEN_DIR,
#         safe_email,
#         "token.json"
#     )
def get_token_path(device_id: str, email: str = None) -> str:
    if email:
        safe_email = encode_email_for_path(email)
        return os.path.join(TOKEN_DIR, device_id, safe_email, "token.json")
    return os.path.join(TOKEN_DIR, device_id, "token.json")

# ---------------------------------------------------
# ENSURE TOKEN DIR
# ---------------------------------------------------
def ensure_token_dir_exists():

    os.makedirs(
        TOKEN_DIR,
        exist_ok=True
    )


# ---------------------------------------------------
# LOAD EXISTING ACCOUNTS
# ---------------------------------------------------
def load_existing_accounts():

    ensure_token_dir_exists()

    existing_emails = set()

    for folder in os.listdir(TOKEN_DIR):

        token_path = os.path.join(
            TOKEN_DIR,
            folder,
            "token.json"
        )

        if os.path.exists(token_path):

            decoded_email = decode_path_to_email(
                folder
            )

            existing_emails.add(
                decoded_email
            )

    return sorted(existing_emails)


# ---------------------------------------------------
# CLEAN DUPLICATE TOKENS
# ---------------------------------------------------
def clean_duplicate_tokens_safe(
    base_path=TOKEN_DIR
):

    if not os.path.exists(base_path):

        return

    seen = {}

    for folder in os.listdir(base_path):

        try:

            email = decode_path_to_email(
                folder
            )

            if email in seen:

                dup_path = os.path.join(
                    base_path,
                    folder
                )

                shutil.rmtree(
                    dup_path,
                    onerror=remove_readonly
                )

            else:

                seen[email] = folder

        except Exception:

            continue


# ---------------------------------------------------
# REMOVE READONLY
# ---------------------------------------------------
def remove_readonly(
    func,
    path,
    _
):

    os.chmod(
        path,
        stat.S_IWRITE
    )

    func(path)
