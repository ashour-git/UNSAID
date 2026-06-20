import re


_COMMON_PASSWORDS: set[str] = {
    "password",
    "password123",
    "12345678",
    "123456789",
    "1234567890",
    "qwerty",
    "qwerty123",
    "qwertyuiop",
    "abc123",
    "abcdef",
    "letmein",
    "admin",
    "admin123",
    "welcome",
    "welcome1",
    "monkey",
    "dragon",
    "master",
    "football",
    "baseball",
    "iloveyou",
    "trustno1",
    "sunshine",
    "princess",
    "shadow",
    "superman",
    "batman",
    "password1",
    "passw0rd",
    "p@ssword",
    "p@ssw0rd",
    "changeme",
    "secret",
    "unknown",
    "access",
    "pass123",
    "login",
    "hello",
    "starwars",
    "zaq1zaq1",
    "1qaz2wsx",
    "asdfghjkl",
    "zxcvbnm",
    "00000000",
    "11111111",
    "12121212",
}


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, None


def is_common_password(password: str) -> bool:
    return password.lower() in _COMMON_PASSWORDS