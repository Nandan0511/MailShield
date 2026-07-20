from oauth_google import get_redirect_uri
from config import CLIENT_ID, CLIENT_SECRET
from config import get_config

code = get_config("AUTHORIZATION_CODE")

print("CLIENT_ID:", CLIENT_ID)
print("CLIENT_SECRET starts with:", CLIENT_SECRET[:10])
print("REDIRECT:", get_redirect_uri())
print("CODE:", code[:20])