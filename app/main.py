"""FastAPI entry point for the Expense Splitter application."""

from fastapi import FastAPI


app = FastAPI(title="Expense Splitter")


@app.get("/")
def read_root() -> dict[str, str]:
    """Identify the application."""
    return {"name": "Expense Splitter"}


@app.get("/api/health")
def read_health() -> dict[str, str]:
    """Report whether the API is available."""
    return {"status": "ok"}
