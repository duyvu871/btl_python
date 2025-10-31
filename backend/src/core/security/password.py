from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class PasswordManager:
    """
    Class xử lý password sử dụng Argon2 để hash và verify.
    """

    def __init__(self):
        self.hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify_password(self, hashed_password: str, password: str) -> bool:
        try:
            self.hasher.verify(hashed_password, password)
            return True
        except VerifyMismatchError:
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        return self.hasher.check_needs_rehash(hashed_password)
