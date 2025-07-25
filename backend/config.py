from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application configuration using Pydantic.
    Loads settings from environment variables and/or a .env file.
    """
    # Define your application's settings with type hints.
    # Pydantic will automatically read them from the environment.
    
    # Database URL. Default is a local SQLite DB for development.
    # For production, this should be set to a PostgreSQL or other production DB URL.
    DATABASE_URL: str
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # Token expiry time

    # Model configuration
    # This tells pydantic-settings to look for a .env file
    model_config = SettingsConfigDict(env_file=".env")


# Create a single instance of the settings to be used throughout the application
settings = Settings()
