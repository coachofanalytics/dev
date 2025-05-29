import secrets
import string
from core.domain.authenticator.jwt_token import create_access_token

print(create_access_token())

def generate_secret_key(length=64):
    """Generate a secure secret key.
    
    Args:
        length (int): Length of the secret key. Default is 64 characters.
    
    Returns:
        str: A secure secret key
    """
    # Define character sets
    alphabet = string.ascii_letters + string.digits + string.punctuation
    
    # Generate the key
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return secret_key

if __name__ == "__main__":
    # Generate keys for different environments
    print("\nDevelopment Secret Key:")
    print(generate_secret_key())
    
    print("\nStaging Secret Key:")
    print(generate_secret_key())
    
    print("\nProduction Secret Key:")
    print(generate_secret_key()) 