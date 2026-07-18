import os


def _get_api_key():
    return (
        os.getenv("GEMINI_API_KEY","AIzaSyD1INKL6rb1AccyIXSkGzTfjYrOboHQZ4Q")
        or os.getenv("API_KEY")
    )


api_key = _get_api_key()