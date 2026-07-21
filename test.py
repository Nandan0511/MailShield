from config import (
    CLIENT_ID,
    SCOPES,

    get_redirect_uri,
)
print("CLIENT_ID:", CLIENT_ID)
print("REDIRECT_URI:", get_redirect_uri())
print("SCOPES:", SCOPES)