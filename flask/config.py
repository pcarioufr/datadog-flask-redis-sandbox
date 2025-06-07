import os

class Config:

    # FLASK ###############
    SECRET_KEY = os.environ.get("FLASK_SECRET")

    # REDIS ###############
    REDIS_HOST = os.environ.get("REDIS_HOST")

    # OLLAMA ###############
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")  # default to mistral if not set
    OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.8"))  # default to 0.8
    OLLAMA_TOP_P = float(os.environ.get("OLLAMA_TOP_P", "0.9"))  # default to 0.9
    OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", 512))  # default to 512
    OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", 4096))  # default to 4096

    # DATADOG ###############
    DD_CLIENT_TOKEN = os.environ.get("DD_CLIENT_TOKEN")
    DD_APPLICATION_ID = os.environ.get("DD_APPLICATION_ID")
    DD_VERSION = os.environ.get("DD_VERSION")
    DD_ENV = os.environ.get("DD_ENV")
    DD_SITE = os.environ.get("DD_SITE")
