"""User-friendly launcher for the Expense Splitter web application."""

import threading
import webbrowser

import uvicorn

from app.main import app


HOST = "127.0.0.1"
PORT = 8000
APP_URL = f"http://{HOST}:{PORT}"


def open_browser() -> None:
    """Open the application in the user's default browser."""
    webbrowser.open(APP_URL)


if __name__ == "__main__":
    browser_timer = threading.Timer(1.0, open_browser)
    browser_timer.daemon = True
    browser_timer.start()
    uvicorn.run(app, host=HOST, port=PORT)
