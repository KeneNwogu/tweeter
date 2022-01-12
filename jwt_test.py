import secrets

# token = jwt.encode({"user_id": 1}, "secret", "HS256")
# print(token)
#
# payload = jwt.decode(token, "secret", "HS256")
# print(payload)

print(secrets.token_hex(6))
