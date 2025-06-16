import os

def validate_int_in_range(value, min_val, max_val, name):
    """Validate an integer is within a range."""
    try:
        val = int(value)
        if not (min_val <= val <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val}")
        return val
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid integer between {min_val} and {max_val}")

class Config:

    # FLASK ###############
    SECRET_KEY = os.environ.get("FLASK_SECRET")

    # REDIS ###############
    REDIS_HOST = os.environ.get("REDIS_HOST")

    # OLLAMA ###############
    OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.8"))  # default to 0.8
    OLLAMA_TOP_P = float(os.environ.get("OLLAMA_TOP_P", "0.9"))  # default to 0.9
    
    # Validate num_predict (reasonable range: 64 to 2048)
    OLLAMA_NUM_PREDICT = validate_int_in_range(
        os.environ.get("OLLAMA_NUM_PREDICT", 512),
        min_val=64,
        max_val=2048,
        name="OLLAMA_NUM_PREDICT"
    )
    
    # Validate num_ctx (reasonable range: 512 to 8192)
    OLLAMA_NUM_CTX = validate_int_in_range(
        os.environ.get("OLLAMA_NUM_CTX", 4096),
        min_val=512,
        max_val=8192,
        name="OLLAMA_NUM_CTX"
    )
    
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST")

    # TEST VARIABLES ###############
    TEST_OLLAMA_DOWN = os.environ.get("TEST_OLLAMA_DOWN", "false").lower() in ("true", "1", "yes")
    TEST_OLLAMA_NOMODEL = os.environ.get("TEST_OLLAMA_NOMODEL", "false").lower() in ("true", "1", "yes")

    # DATADOG ###############
    DD_CLIENT_TOKEN = os.environ.get("DD_CLIENT_TOKEN")
    DD_APPLICATION_ID = os.environ.get("DD_APPLICATION_ID")
    DD_VERSION = os.environ.get("DD_VERSION")
    DD_ENV = os.environ.get("DD_ENV")
    DD_SITE = os.environ.get("DD_SITE")
