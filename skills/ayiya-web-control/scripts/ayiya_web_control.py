#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CHROME_PATH = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
DEFAULT_BASE_DIR = Path(r"C:\temp\ayiya-web-control")
RISK_PATTERNS = (
    "captcha",
    "hcaptcha",
    "recaptcha",
    "cf-challenge",
    "verify you are human",
    "too many requests",
    "rate limit",
    "rate limited",
    "unusual traffic",
    "suspicious activity",
    "access denied",
    "验证码",
    "人机验证",
    "访问过于频繁",
    "请求过于频繁",
    "账号风险",
)


class RiskControlStop(RuntimeError):
    pass


def slugify(value: str) -> str:
    value = value.strip().lower()
    if "://" in value:
        parsed = urllib.parse.urlparse(value)
        value = parsed.netloc or parsed.path
    value = re.sub(r"^www\.", "", value)
    value = re.sub(r"[^a-z0-9.-]+", "-", value)
    value = value.strip(".-")
    return value[:80] or "site"


def profile_dir_for(site_key: str, base_dir: Path = DEFAULT_BASE_DIR) -> Path:
    return base_dir / slugify(site_key) / "profile"


def find_chrome(explicit: Path | None = None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(
        [
            DEFAULT_CHROME_PATH,
            Path(os.environ.get("LOCALAPPDATA", "")) / r"Google\Chrome\Application\chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / r"Google\Chrome\Application\chrome.exe",
        ]
    )
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    found = shutil.which("chrome") or shutil.which("chrome.exe")
    if found:
        return Path(found)
    raise SystemExit("Chrome not found. Pass --chrome-path explicitly.")


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def emit(data: Any, use_json: bool = True) -> None:
    if use_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data)


def pace(min_ms: int = 120, max_ms: int = 420) -> None:
    time.sleep(random.uniform(min_ms, max_ms) / 1000)


def launch_chrome(
    chrome_path: Path,
    profile_dir: Path,
    url: str,
    port: int | None = None,
    headed_login: bool = False,
    window_size: str = "1440,1200",
    window_position: str = "-2400,0",
) -> subprocess.Popen:
    profile_dir.mkdir(parents=True, exist_ok=True)
    args = [
        str(chrome_path),
        f"--user-data-dir={profile_dir}",
        "--profile-directory=Default",
        "--lang=zh-CN",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--hide-crash-restore-bubble",
        "--new-window",
    ]
    if port:
        args.append(f"--remote-debugging-port={port}")
    if not headed_login:
        args.extend([f"--window-size={window_size}", f"--window-position={window_position}"])
    args.append(url)
    return subprocess.Popen(args)


def import_playwright():
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Playwright is not installed for this Python. Run: python -m pip install playwright"
        ) from exc
    return sync_playwright, PlaywrightTimeoutError


def connect_page(profile_dir: Path, url: str, chrome_path: Path, args: argparse.Namespace):
    sync_playwright, _ = import_playwright()
    port = args.port or find_free_port()
    proc = launch_chrome(
        chrome_path=chrome_path,
        profile_dir=profile_dir,
        url=url,
        port=port,
        headed_login=False,
        window_size=args.window_size,
        window_position=args.window_position,
    )
    time.sleep(args.launch_wait)
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    context = browser.contexts[0]
    page = None
    for candidate in context.pages:
        if candidate.url and candidate.url != "about:blank":
            page = candidate
            break
    if page is None:
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=args.timeout)
    return pw, browser, proc, page


def shutdown(pw, browser, proc: subprocess.Popen, keep_browser: bool = False) -> None:
    try:
        browser.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass
    if keep_browser:
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def page_risk_reason(page) -> str | None:
    try:
        url = page.url.lower()
        title = page.title().lower()
        body = page.locator("body").inner_text(timeout=2000).lower()
    except Exception:
        return None
    haystack = "\n".join([url, title, body[:12000]])
    for pattern in RISK_PATTERNS:
        if pattern.lower() in haystack:
            return pattern
    return None


def ensure_no_risk_control(page) -> None:
    reason = page_risk_reason(page)
    if reason:
        raise RiskControlStop(f"Risk-control marker detected: {reason}")


def close_transient_overlays(page) -> None:
    selectors = [
        '[aria-label="Close"]',
        'button[aria-label="Close"]',
        'button[title="Close"]',
        "button:has-text('Close')",
        "button:has-text('关闭')",
    ]
    for selector in selectors:
        try:
            loc = page.locator(selector)
            if loc.count():
                loc.first.click(timeout=1500)
                pace(250, 600)
                return
        except Exception:
            continue
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def stable_click(page, selector: str, timeout: int) -> None:
    _, PlaywrightTimeoutError = import_playwright()
    loc = page.locator(selector).first
    last_error = None
    for attempt in range(3):
        close_transient_overlays(page)
        try:
            loc.wait_for(state="visible", timeout=timeout)
            loc.scroll_into_view_if_needed(timeout=timeout)
            pace()
            loc.hover(timeout=timeout)
            pace()
            loc.click(timeout=timeout, force=(attempt == 2))
            ensure_no_risk_control(page)
            return
        except PlaywrightTimeoutError as exc:
            last_error = exc
            pace(500, 1100)
    if last_error:
        raise last_error


def fill_value(page, selector: str, value: str, timeout: int, by_typing: bool = False) -> None:
    loc = page.locator(selector).first
    loc.wait_for(state="visible", timeout=timeout)
    loc.scroll_into_view_if_needed(timeout=timeout)
    loc.click(timeout=timeout)
    if by_typing:
        page.keyboard.press("Control+A")
        pace()
        page.keyboard.type(value, delay=random.randint(20, 80))
    else:
        loc.fill(value, timeout=timeout)
    ensure_no_risk_control(page)


def inspect_page(page) -> dict[str, Any]:
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    pace(600, 1200)
    ensure_no_risk_control(page)
    data = page.evaluate(
        """
        () => {
          const pick = (nodes, mapper, limit = 80) => Array.from(nodes).slice(0, limit).map(mapper);
          const text = (el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim();
          return {
            url: location.href,
            title: document.title,
            body_text_sample: (document.body?.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 5000),
            links: pick(document.querySelectorAll('a[href]'), a => ({text: text(a).slice(0, 120), href: a.href}), 120),
            buttons: pick(document.querySelectorAll('button,[role="button"]'), b => ({
              text: text(b).slice(0, 120),
              aria: b.getAttribute('aria-label') || '',
              testid: b.getAttribute('data-testid') || '',
              id: b.id || ''
            }), 120),
            inputs: pick(document.querySelectorAll('input, textarea, select'), i => ({
              tag: i.tagName.toLowerCase(),
              type: i.getAttribute('type') || '',
              name: i.getAttribute('name') || '',
              placeholder: i.getAttribute('placeholder') || '',
              aria: i.getAttribute('aria-label') || '',
              id: i.id || '',
              testid: i.getAttribute('data-testid') || ''
            }), 120),
            forms: document.forms.length
          };
        }
        """
    )
    return data


def action_value(step: dict[str, Any]) -> str:
    if "value" in step:
        return str(step["value"])
    if "value_env" in step:
        name = str(step["value_env"])
        if name not in os.environ:
            raise RuntimeError(f"Environment variable not set: {name}")
        return os.environ[name]
    return ""


def run_step(page, step: dict[str, Any], state: dict[str, Any], download_dir: Path, timeout: int) -> None:
    action = step["action"]
    selector = step.get("selector")

    if action == "goto":
        page.goto(step["url"], wait_until=step.get("wait_until", "domcontentloaded"), timeout=timeout)
        ensure_no_risk_control(page)
    elif action == "click":
        stable_click(page, selector, timeout)
    elif action == "fill":
        fill_value(page, selector, action_value(step), timeout, by_typing=False)
    elif action == "type":
        fill_value(page, selector, action_value(step), timeout, by_typing=True)
    elif action == "press":
        if selector:
            page.locator(selector).first.click(timeout=timeout)
        page.keyboard.press(step["key"])
        ensure_no_risk_control(page)
    elif action == "upload":
        path = Path(step["path"]).resolve()
        if not path.is_file():
            raise RuntimeError(f"Upload file not found: {path}")
        page.locator(selector).first.set_input_files(str(path), timeout=timeout)
        ensure_no_risk_control(page)
    elif action == "wait_for_selector":
        page.wait_for_selector(selector, state=step.get("state", "visible"), timeout=timeout)
        ensure_no_risk_control(page)
    elif action == "wait_for_url":
        page.wait_for_url(step["url"], timeout=timeout)
        ensure_no_risk_control(page)
    elif action == "download_click":
        download_dir.mkdir(parents=True, exist_ok=True)
        with page.expect_download(timeout=timeout) as download_info:
            stable_click(page, selector, timeout)
        download = download_info.value
        suggested = download.suggested_filename or f"{step['id']}.bin"
        target = download_dir / step.get("filename", suggested)
        download.save_as(str(target))
        state.setdefault("downloads", {})[step["id"]] = str(target)
    elif action == "extract_text":
        texts = page.locator(selector).all_inner_texts()
        state.setdefault("values", {})[step.get("save_as", step["id"])] = texts
    elif action == "extract_attr":
        attr = step["attribute"]
        values = page.locator(selector).evaluate_all(
            "(els, attr) => els.map(el => el.getAttribute(attr) || '')",
            attr,
        )
        state.setdefault("values", {})[step.get("save_as", step["id"])] = values
    elif action == "screenshot":
        target = Path(step.get("path", f"{step['id']}.png")).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target), full_page=bool(step.get("full_page", True)))
        state.setdefault("screenshots", {})[step["id"]] = str(target)
    elif action == "scroll":
        page.mouse.wheel(int(step.get("dx", 0)), int(step.get("dy", 900)))
        pace(500, 1200)
    elif action == "sleep":
        time.sleep(float(step.get("seconds", 1)))
    else:
        raise RuntimeError(f"Unsupported action: {action}")


def cmd_doctor(args: argparse.Namespace) -> int:
    chrome = find_chrome(args.chrome_path)
    try:
        import_playwright()
        playwright = "ok"
    except SystemExit as exc:
        playwright = str(exc)
    emit(
        {
            "python": sys.executable,
            "chrome": str(chrome),
            "playwright": playwright,
            "base_dir": str(DEFAULT_BASE_DIR),
        }
    )
    return 0 if playwright == "ok" else 1


def cmd_profile(args: argparse.Namespace) -> int:
    emit({"site_key": slugify(args.site_key), "profile_dir": str(profile_dir_for(args.site_key))})
    return 0


def cmd_launch_login(args: argparse.Namespace) -> int:
    chrome = find_chrome(args.chrome_path)
    profile_dir = args.profile_dir or profile_dir_for(args.site_key)
    proc = launch_chrome(chrome, profile_dir, args.url, headed_login=True)
    emit(
        {
            "mode": "manual-login",
            "pid": proc.pid,
            "site_key": slugify(args.site_key),
            "profile_dir": str(profile_dir),
            "url": args.url,
            "next": "Log in manually, complete MFA/CAPTCHA if shown, close Chrome, then rerun the automation.",
        }
    )
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    chrome = find_chrome(args.chrome_path)
    profile_dir = args.profile_dir or profile_dir_for(args.site_key)
    pw = browser = proc = None
    try:
        pw, browser, proc, page = connect_page(profile_dir, args.url, chrome, args)
        data = inspect_page(page)
        if args.screenshot:
            screenshot = Path(args.screenshot).resolve()
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=True)
            data["screenshot"] = str(screenshot)
        if args.output:
            write_json(Path(args.output), data)
        emit(data)
        return 0
    except RiskControlStop as exc:
        emit({"status": "stopped", "reason": str(exc)})
        return 2
    finally:
        if pw is not None:
            shutdown(pw, browser, proc, keep_browser=args.keep_browser)


def cmd_run_plan(args: argparse.Namespace) -> int:
    chrome = find_chrome(args.chrome_path)
    profile_dir = args.profile_dir or profile_dir_for(args.site_key)
    plan_path = Path(args.plan).resolve()
    state_path = Path(args.state).resolve()
    plan = read_json(plan_path, [])
    if not isinstance(plan, list):
        raise SystemExit("Plan file must contain a JSON array of steps.")
    state = read_json(state_path, {"completed_steps": [], "values": {}, "downloads": {}})
    completed = set(state.get("completed_steps", []))
    url = args.url or next((step.get("url") for step in plan if step.get("action") == "goto"), "about:blank")
    if args.dry_run:
        emit(
            {
                "status": "dry-run",
                "site_key": slugify(args.site_key),
                "profile_dir": str(profile_dir),
                "state": str(state_path),
                "steps": [
                    {
                        "id": step.get("id"),
                        "action": step.get("action"),
                        "skipped": step.get("id") in completed,
                    }
                    for step in plan
                ],
            }
        )
        return 0
    pw = browser = proc = None
    try:
        pw, browser, proc, page = connect_page(profile_dir, url, chrome, args)
        for step in plan:
            step_id = step.get("id")
            if not step_id:
                raise RuntimeError(f"Step missing id: {step}")
            if step_id in completed:
                continue
            run_step(page, step, state, Path(args.download_dir), args.timeout)
            completed.add(step_id)
            state["completed_steps"] = sorted(completed)
            state["last_step"] = step_id
            state["last_url"] = page.url
            write_json(state_path, state)
            print(f"[done] {step_id}", flush=True)
        emit({"status": "completed", "state": str(state_path), "completed_steps": sorted(completed)})
        return 0
    except RiskControlStop as exc:
        state["stopped"] = {"reason": str(exc), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        write_json(state_path, state)
        emit({"status": "stopped", "reason": str(exc), "state": str(state_path)})
        return 2
    except Exception as exc:
        state["last_error"] = str(exc)
        state["last_error_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        write_json(state_path, state)
        raise
    finally:
        if pw is not None:
            shutdown(pw, browser, proc, keep_browser=args.keep_browser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AyIYA generic web-control helper.")
    parser.add_argument("--chrome-path", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--chrome-path", type=Path, default=None)
    doctor.set_defaults(func=cmd_doctor)

    profile = sub.add_parser("profile")
    profile.add_argument("--site-key", required=True)
    profile.set_defaults(func=cmd_profile)

    login = sub.add_parser("launch-login")
    login.add_argument("--site-key", required=True)
    login.add_argument("--url", required=True)
    login.add_argument("--profile-dir", type=Path, default=None)
    login.add_argument("--chrome-path", type=Path, default=None)
    login.set_defaults(func=cmd_launch_login)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--site-key", required=True)
    common.add_argument("--profile-dir", type=Path, default=None)
    common.add_argument("--chrome-path", type=Path, default=None)
    common.add_argument("--port", type=int, default=0)
    common.add_argument("--timeout", type=int, default=60000)
    common.add_argument("--launch-wait", type=float, default=5.0)
    common.add_argument("--window-size", default="1440,1200")
    common.add_argument("--window-position", default="-2400,0")
    common.add_argument("--keep-browser", action="store_true")

    inspect = sub.add_parser("inspect", parents=[common])
    inspect.add_argument("--url", required=True)
    inspect.add_argument("--output", default="")
    inspect.add_argument("--screenshot", default="")
    inspect.set_defaults(func=cmd_inspect)

    run_plan = sub.add_parser("run-plan", parents=[common])
    run_plan.add_argument("--url", default="")
    run_plan.add_argument("--plan", required=True)
    run_plan.add_argument("--state", required=True)
    run_plan.add_argument("--download-dir", default="downloads")
    run_plan.add_argument("--dry-run", action="store_true")
    run_plan.set_defaults(func=cmd_run_plan)

    return parser


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
