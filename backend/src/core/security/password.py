from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasher = PasswordHasher()

# hash a password
def hash_password(password: str) -> str:
    return hasher.hash(password)

# verify a password against a hash
def verify_password(hashed_password: str, password: str) -> bool:
    try:
        hasher.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False

# check if a hashed password needs rehashing
def needs_rehash(hashed_password: str) -> bool:
    return hasher.check_needs_rehash(hashed_password)
