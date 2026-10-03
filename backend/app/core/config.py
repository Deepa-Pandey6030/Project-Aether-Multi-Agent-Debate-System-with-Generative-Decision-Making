"""
Configuration settings for AETHER system
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AETHER"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Groq API Configuration (from environment)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Gemini API Configuration (used for neutral summarization)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # MongoDB
    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "aether"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-long-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_AGENT_CONVERSATION: bool = True
    LOG_LLM_PROMPTS: bool = False
    LOG_LLM_RESPONSES: bool = False
    LOG_LLM_MAX_CHARS: int = 4000

    # Time Budgets (in seconds)
    DEFAULT_TIME_BUDGET: int = 600
    MIN_TIME_BUDGET: int = 300
    MAX_TIME_BUDGET: int = 1200

    # Time Allocation Percentages
    TIME_FACTOR_EXTRACTION: float = 0.08
    TIME_OPENING_STATEMENTS: float = 0.17
    TIME_REBUTTAL_ROUNDS: float = 0.35
    TIME_CROSS_EXAMINATION: float = 0.20
    TIME_CLOSING_STATEMENTS: float = 0.10
    TIME_SYNTHESIS: float = 0.10

    # Agent Configuration
    MAX_FACTORS: int = 5

    # Rebuttal Round Configuration
    MIN_DEBATE_ROUNDS: int = 1
    MAX_DEBATE_ROUNDS: int = 4
    ROUND_EVALUATION_ENABLED: bool = True

    # Cross-Examination Configuration
    CROSS_EXAM_ALWAYS_ENABLED: bool = True
    MAX_CROSS_EXAM_QUESTIONS_PER_AGENT: int = 5

    # Closing Statements
    CLOSING_STATEMENTS_ENABLED: bool = True
    CLOSING_STATEMENTS_MIN_TIME: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()