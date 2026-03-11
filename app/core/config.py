import os
from dotenv import load_dotenv

load_dotenv()

# GitLab
GITLAB_URL = os.getenv("GITLAB_URL", "")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")

# DB
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "projectlens")
DB_PASSWORD = os.getenv("DB_PASSWORD", "projectlens")
DB_NAME = os.getenv("DB_NAME", "projectlens")
