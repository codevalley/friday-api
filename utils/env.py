import os


def get_env_filename() -> str:
    """Get the environment file name based on the runtime environment."""
    runtime_env = os.getenv("ENV")
    return f".env.{runtime_env}" if runtime_env else ".env"
