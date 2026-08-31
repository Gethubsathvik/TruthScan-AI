from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI News Verification"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite:///./verification.db"
    DATABASE_URL_ASYNC: str = "sqlite+aiosqlite:///./verification.db"
    
    OPENAI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None
    BRAVE_SEARCH_API_KEY: Optional[str] = None
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    MAX_ARTICLE_LENGTH: int = 50000
    REQUEST_TIMEOUT: int = 30
    SEARCH_TIMEOUT: int = 15
    MAX_SEARCH_RESULTS: int = 10
    CACHE_TTL_SECONDS: int = 3600
    
    RATE_LIMIT_PER_MINUTE: int = 60
    
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
