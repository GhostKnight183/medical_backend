from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent

class JWT_AES_Settings(BaseSettings):
    private_key : Path = BASE_DIR / "ssl_jwtkey_aes" / "key" / "jwt-private.pem"
    public_key : Path =  BASE_DIR / "ssl_jwtkey_aes" / "key" / "jwt-public.pem"
    aes_key : Path = BASE_DIR / "ssl_jwtkey_aes" / "aes" / "aes.key"
    access_token_time : int = 15
    refresh_token_time : int  = 30 
    email_token_time : int = 20
    algorithm : str = "RS256"
    access_token : str = "access_token"
    refresh_token : str = "refresh_token"
    change_pass_token : str = "change_pass_token"
    delete_account_token : str = "delete_account_token"
    verified_email_token : str = "verified_email_token"

jwt_aes_settings = JWT_AES_Settings()
