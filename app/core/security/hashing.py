from werkzeug.security import generate_password_hash, check_password_hash

def get_password_hash(password: str) -> str:

    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    return check_password_hash(hashed_password, plain_password)