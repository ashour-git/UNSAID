import os


def handler(request):
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": "{\"ok\":true,\"has_database_url\":%s,\"has_session_secret\":%s}" % (
            "true" if os.getenv("DATABASE_URL") else "false",
            "true" if os.getenv("SESSION_SECRET_KEY") else "false",
        ),
    }
