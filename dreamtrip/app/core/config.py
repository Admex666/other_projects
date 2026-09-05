import os
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)

STATIC_DIR = os.path.join(ROOT_DIR, "static")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = (APP_ENV == "production")

def get_clarity_project_id() -> str:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv("CLARITY_PROJECT_ID", "").strip().strip('"').strip("'")

class DynamicClarityId:
    def __str__(self):
        return get_clarity_project_id()
    def __bool__(self):
        return bool(get_clarity_project_id())
    def __html__(self):
        return get_clarity_project_id()

CLARITY_PROJECT_ID = get_clarity_project_id()

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals["clarity_project_id"] = DynamicClarityId()

