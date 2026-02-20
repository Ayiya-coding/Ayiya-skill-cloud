import json
import os
import subprocess
import threading
import time
from collections import deque

from flask import Flask, jsonify, render_template

ROOT = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(ROOT, "config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


config = load_config()
WORKING_DIR = os.path.abspath(os.path.join(ROOT, config.get("working_dir", "..")))
INSTALL_CMD = config.get("install_cmd", "SKIP")
RUN_CMD = config.get("run_cmd", "SKIP")
APP_URL = config.get("app_url", "")
WEBUI_PORT = int(config.get("webui_port", 7860))

log_lines = deque(maxlen=600)
proc = None
proc_lock = threading.Lock()


def append_log(line):
    ts = time.strftime("%H:%M:%S")
    log_lines.append(f"[{ts}] {line}")


def run_install():
    if not INSTALL_CMD or INSTALL_CMD == "SKIP":
        append_log("Install command is SKIP.")
        return 0
    append_log(f">>> {INSTALL_CMD}")
    result = subprocess.run(
        INSTALL_CMD,
        cwd=WORKING_DIR,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.stdout:
        for line in result.stdout.splitlines():
            append_log(line)
    append_log(f"Install exited with code {result.returncode}.")
    return result.returncode


def _read_proc_output(p):
    for line in p.stdout:
        append_log(line.rstrip())
    code = p.wait()
    append_log(f"Run process exited with code {code}.")


def start_run():
    global proc
    if not RUN_CMD or RUN_CMD == "SKIP":
        append_log("Run command is SKIP.")
        return False
    with proc_lock:
        if proc and proc.poll() is None:
            append_log("Run process already running.")
            return True
        append_log(f">>> {RUN_CMD}")
        proc = subprocess.Popen(
            RUN_CMD,
            cwd=WORKING_DIR,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        t = threading.Thread(target=_read_proc_output, args=(proc,), daemon=True)
        t.start()
        return True


def stop_run():
    global proc
    with proc_lock:
        if not proc or proc.poll() is not None:
            append_log("No running process.")
            return False
        append_log("Stopping process...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            append_log("Force killing process...")
            proc.kill()
        return True


app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template(
        "index.html",
        app_url=APP_URL,
        has_install=bool(INSTALL_CMD and INSTALL_CMD != "SKIP"),
        has_run=bool(RUN_CMD and RUN_CMD != "SKIP"),
    )


@app.route("/api/install", methods=["POST"])
def api_install():
    code = run_install()
    return jsonify({"ok": code == 0})


@app.route("/api/start", methods=["POST"])
def api_start():
    ok = start_run()
    return jsonify({"ok": ok})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    ok = stop_run()
    return jsonify({"ok": ok})


@app.route("/api/status")
def api_status():
    running = proc is not None and proc.poll() is None
    return jsonify({"running": running})


@app.route("/api/logs")
def api_logs():
    return jsonify({"lines": list(log_lines)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=WEBUI_PORT, debug=False)
