import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ACCEPTS = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    APP_ROOT = os.getenv("APP_ROOT")
    FILE_BASE = os.environ.get("FILE_BASE", "/var/data/doc-data/")
    STATIC_FOLDER_PATH = "resources"

    @staticmethod
    def get_static_url_path() -> str:
        if Config.APP_ROOT.endswith("/"):
            prefix_with_end_slash = Config.APP_ROOT
        else:
            prefix_with_end_slash = Config.APP_ROOT + "/"
        # check if APP_ROOT startswith '/'
        if Config.APP_ROOT.startswith("/"):
            prefix = prefix_with_end_slash
        else:
            prefix = "/" + prefix_with_end_slash

        return prefix + Config.STATIC_FOLDER_PATH
