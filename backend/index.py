"""
Vercel Python entrypoint for the NEXUS FastAPI backend.

Vercel imports this module and looks for a module-level ASGI app named `app`.

If importing the real app raises, we do NOT let the exception escape — that
produces an opaque FUNCTION_INVOCATION_FAILED with the traceback buried in
runtime logs. Instead we mount a tiny diagnostic app that serves the real
traceback at `/` so you can read it in the browser.

Once the app imports cleanly the diagnostic path is never used.
"""
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT, "backend", "app")

# Order matters: `backend/app` first, because every router uses flat absolute
# imports (`from schemas import ...`) rather than package-relative ones.
for _path in (APP_DIR, os.path.join(ROOT, "backend"), ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

_IMPORT_ERROR = None

try:
    from main import app
except BaseException:  # noqa: BLE001 - we must catch SystemExit/MemoryError too
    _IMPORT_ERROR = traceback.format_exc()

if _IMPORT_ERROR is not None:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse, PlainTextResponse

    app = FastAPI(title="NEXUS — import diagnostics")

    def _environment_report() -> dict:
        """Everything needed to tell the four failure modes apart."""
        return {
            "python_version": sys.version,
            "cwd": os.getcwd(),
            "entrypoint_dir": os.path.dirname(os.path.abspath(__file__)),
            "resolved_root": ROOT,
            "expected_app_dir": APP_DIR,
            "app_dir_exists": os.path.isdir(APP_DIR),
            "main_py_exists": os.path.isfile(os.path.join(APP_DIR, "main.py")),
            "root_listing": _safe_listdir(ROOT),
            "backend_listing": _safe_listdir(os.path.join(ROOT, "backend")),
            "app_listing": _safe_listdir(APP_DIR),
            "sys_path_head": sys.path[:6],
            "env_present": {
                key: bool(os.getenv(key))
                for key in (
                    "DATABASE_URL",
                    "CORS_ALLOWED_ORIGINS",
                    "ENV",
                    "REDIS_URL",
                )
            },
            "installed_heavy_packages": _installed(
                [
                    "fastapi",
                    "pydantic",
                    "sqlalchemy",
                    "psycopg2",
                    "numpy",
                    "pymoo",
                    "shapely",
                    "pyproj",
                    "PIL",
                    "redis",
                    "pystac_client",
                ]
            ),
        }

    def _safe_listdir(path: str):
        try:
            return sorted(os.listdir(path))[:40]
        except Exception as exc:  # noqa: BLE001
            return f"<unreadable: {exc}>"

    def _installed(names):
        import importlib.util

        out = {}
        for name in names:
            try:
                out[name] = importlib.util.find_spec(name) is not None
            except Exception:  # noqa: BLE001
                out[name] = False
        return out

    @app.get("/", response_class=PlainTextResponse)
    def diagnose_plain():
        report = _environment_report()
        lines = [
            "NEXUS BACKEND FAILED TO IMPORT",
            "=" * 60,
            "",
            "TRACEBACK",
            "-" * 60,
            _IMPORT_ERROR,
            "",
            "ENVIRONMENT",
            "-" * 60,
        ]
        for key, value in report.items():
            lines.append(f"{key}: {value}")
        lines += [
            "",
            "READ THE LAST LINE OF THE TRACEBACK:",
            "-" * 60,
            "  ModuleNotFoundError: No module named 'schemas'/'database'/"
            "'routers'/'mapdata'",
            "     -> sys.path is wrong. Check app_dir_exists and main_py_exists",
            "        above; your repo layout differs from what index.py assumes.",
            "",
            "  ModuleNotFoundError: No module named 'numpy'/'pymoo'/'sqlalchemy'",
            "     -> requirements.txt was not installed. It MUST be at the repo",
            "        ROOT, not in backend/. Check installed_heavy_packages above.",
            "",
            "  OSError / sqlite3 / 'readonly database' / 'unable to open'",
            "     -> the SQLite fallback is writing to a read-only disk.",
            "        Set DATABASE_URL to a real Postgres instance.",
            "",
            "  OperationalError / could not connect to server / timeout",
            "     -> DATABASE_URL is set but unreachable from Vercel. Confirm the",
            "        host allows external connections and includes ?sslmode=require",
            "",
            "  MemoryError, or no traceback at all + build failure",
            "     -> the bundle exceeded 250 MB. Trim requirements.txt.",
        ]
        return "\n".join(str(line) for line in lines)

    @app.get("/_diagnostics")
    def diagnose_json():
        return JSONResponse(
            {"error": "import_failed", "traceback": _IMPORT_ERROR,
             "environment": _environment_report()},
            status_code=500,
        )

    @app.get("/{path:path}", response_class=PlainTextResponse)
    def catch_all(path: str):
        return diagnose_plain()

handler = app
