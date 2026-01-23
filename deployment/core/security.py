from passlib.context import CryptContext

# Argon2 is modern and avoids bcrypt issues on some Windows/Python builds
_pwd = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    password = (password or "").strip()
    return _pwd.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    password = (password or "").strip()
    return _pwd.verify(password, password_hash)
