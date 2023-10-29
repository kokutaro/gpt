import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ACCEPTS = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    FILE_TYPES = [
        "pdf",
        "docx",
        "xlsx",
    ]
    APP_ROOT = os.getenv("APP_ROOT")
    FILE_BASE = os.environ.get("FILE_BASE", "/var/data/doc-data/")
    STATIC_FOLDER_PATH = "resources"
