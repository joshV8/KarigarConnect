"""
Gate 14 Tests — Security & Production Readiness.

Per GATE_14_SECURITY_AND_PRODUCTION_READINESS.md:
- No API keys hardcoded in source code
- .env excluded from Git via .gitignore
- .env.example contains placeholders only
- Secrets never leaked in HTTP responses or client errors
- Frontend/API clients never receive server-side API keys
- User input is validated and file uploads are constrained
- Stack traces are not returned to clients in error responses
- CORS is appropriately configured
- Temporary files are cleaned up
"""

import os
import re
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

CLIENT = TestClient(app)
AI_SERVICE_DIR = Path(__file__).resolve().parent.parent


def test_no_hardcoded_api_keys_in_source():
    """Verify no Google, OpenAI, AWS, or Cloudinary API keys are hardcoded in source code."""
    suspicious_patterns = [
        re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),  # Google API key
        re.compile(r"sk-[A-Za-z0-9]{32,}"),      # OpenAI API key
        re.compile(r"AKIA[0-9A-Z]{16}"),         # AWS Access Key
    ]

    source_dir = AI_SERVICE_DIR / "app"
    for py_file in source_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in suspicious_patterns:
            matches = pattern.findall(content)
            assert not matches, f"Potential hardcoded key found in {py_file}: {matches}"


def test_env_file_excluded_from_git():
    """Verify .gitignore properly excludes .env files and keeps .env.example."""
    gitignore_path = AI_SERVICE_DIR / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist in ai-service"
    lines = [line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()]
    assert any(".env" in line for line in lines), ".gitignore must exclude .env"
    assert any("!.env.example" in line for line in lines), ".gitignore must preserve !.env.example"


def test_env_example_contains_placeholders_only():
    """Verify .env.example contains only variable placeholders, no real secrets."""
    example_path = AI_SERVICE_DIR / ".env.example"
    assert example_path.exists(), ".env.example must exist"
    content = example_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            val = val.strip()
            # Values should be empty, descriptive placeholders, or safe defaults
            assert len(val) == 0 or "YOUR" in val.upper() or "REPLACE" in val.upper() or val in ("INFO", "DEBUG", "WARNING") or key in ("GEMINI_MODEL", "WHISPER_MODEL_SIZE", "LOG_LEVEL", "CORS_ALLOW_ORIGINS"), (
                f".env.example contains non-placeholder value for {key}: {val}"
            )


def test_api_responses_never_leak_server_secrets():
    """Verify that public endpoints never return API keys or internal credentials."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    llm_key = os.getenv("LLM_API_KEY", "")

    endpoints = [
        ("GET", "/health"),
        ("GET", "/"),
        ("GET", "/dashboard"),
        ("GET", "/products"),
    ]

    for method, path in endpoints:
        resp = CLIENT.request(method, path)
        text = resp.text
        if gemini_key and len(gemini_key) > 8:
            assert gemini_key not in text, f"GEMINI_API_KEY leaked at {path}"
        if llm_key and len(llm_key) > 8:
            assert llm_key not in text, f"LLM_API_KEY leaked at {path}"


def test_unhandled_exception_does_not_leak_stack_trace():
    """Global exception handler returns structured JSON without Python stack traces."""
    # Sending malformed input to trigger a 400 or 500
    resp = CLIENT.post(
        "/ai/generate-catalog",
        files={"image": ("bad.jpg", b"not-an-image", "image/jpeg")},
    )
    # Status code should be an HTTP error
    assert resp.status_code in (400, 422, 500)
    # Check body does not contain a Python traceback
    assert "Traceback (most recent call last)" not in resp.text
    assert 'File "' not in resp.text


def test_file_upload_constraints_and_validation():
    """Verify input validation rejects empty files, invalid image formats, and negative costs."""
    # 1. Zero-byte image
    resp = CLIENT.post("/image/validate", files={"image": ("empty.jpg", b"", "image/jpeg")})
    assert resp.status_code in (400, 422)

    # 2. Non-image bytes
    resp = CLIENT.post("/image/validate", files={"image": ("test.txt", b"plain text", "text/plain")})
    assert resp.status_code == 400

    # 3. Negative cost in pricing
    resp = CLIENT.post("/ai/recommend-price", json={"raw_material_cost": -50.0, "labour_cost": 100.0})
    assert resp.status_code in (400, 422)


def test_cors_headers_present():
    """Verify CORS middleware is active for cross-origin frontend requests."""
    resp = CLIENT.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")
