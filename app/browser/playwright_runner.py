from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.browser.autofill import record_autofill_pause, record_autofill_plan, summarise_plan
from app.browser.field_detector import FormField
from app.browser.field_matcher import build_autofill_plan
from app.config.schemas import ProjectConfig
from app.db.models import Application


FIELD_DETECTION_SCRIPT = """
() => {
  const fields = [];
  const controls = Array.from(document.querySelectorAll('input, textarea, select'));
  const cssEscape = window.CSS && CSS.escape ? CSS.escape : (value) => value.replace(/"/g, '\\"');
  function labelFor(el) {
    if (el.id) {
      const label = document.querySelector(`label[for="${cssEscape(el.id)}"]`);
      if (label) return label.innerText.trim();
    }
    const parentLabel = el.closest('label');
    if (parentLabel) return parentLabel.innerText.trim();
    return '';
  }
  function selectorFor(el, index) {
    if (el.id) return `#${cssEscape(el.id)}`;
    if (el.name) return `${el.tagName.toLowerCase()}[name="${cssEscape(el.name)}"]`;
    return `${el.tagName.toLowerCase()}:nth-of-type(${index + 1})`;
  }
  controls.forEach((el, index) => {
    fields.push({
      selector: selectorFor(el, index),
      field_type: el.type || el.tagName.toLowerCase(),
      label: labelFor(el),
      name: el.name || '',
      placeholder: el.placeholder || '',
      aria_label: el.getAttribute('aria-label') || '',
      value: el.value || ''
    });
  });
  return fields;
}
"""

CAPTCHA_DETECTION_SCRIPT = """
() => {
  const text = document.body ? document.body.innerText.toLowerCase() : '';
  const title = document.title ? document.title.toLowerCase() : '';
  const combined = `${title} ${text}`;
  const patterns = [
    'captcha',
    'not a robot',
    '\\u4e0d\\u662f\\u673a\\u5668\\u4eba',
    '\\u9a8c\\u8bc1',
    'verification',
    'bot verification',
    'human verification',
    'temporarily limited',
    'access temporarily limited',
    '\\u7f51\\u9875\\u64cd\\u4f5c\\u884c\\u4e3a\\u786e\\u5b9e\\u51fa\\u81ea\\u60a8\\u672c\\u4eba'
  ];
  return patterns.some(pattern => combined.includes(pattern));
}
"""

ACCESS_LIMIT_DETECTION_SCRIPT = """
() => {
  const text = document.body ? document.body.innerText.toLowerCase() : '';
  const title = document.title ? document.title.toLowerCase() : '';
  const combined = `${title} ${text}`;
  const patterns = [
    'access temporarily limited',
    'temporarily limited',
    'temporarily restricted',
    'unable to operate verification page',
    '\\u8bbf\\u95ee\\u6682\\u65f6\\u53d7\\u9650',
    '\\u7cfb\\u7edf\\u4fa6\\u6d4b\\u5230\\u60a8\\u6d4f\\u89c8\\u7f51\\u9875\\u7684\\u901f\\u5ea6\\u5f02\\u5e38',
    '\\u4e0e\\u7f51\\u8def\\u673a\\u5668\\u4eba\\u76f8\\u540c',
    '\\u65e0\\u6cd5\\u64cd\\u4f5c\\u9a8c\\u8bc1\\u9875\\u9762'
  ];
  return patterns.some(pattern => combined.includes(pattern));
}
"""


def run_playwright_autofill(
    application: Application,
    url: str,
    config: ProjectConfig,
    session: Session,
    headless: bool = False,
    keep_open: bool = False,
    keep_open_seconds: int = 300,
    captcha_wait_seconds: int = 300,
    captcha_poll_seconds: int = 5,
    form_wait_seconds: int = 60,
    form_poll_seconds: int = 2,
) -> dict[str, int]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        _wait_for_network_quiet(page)
        if _is_access_limited_page(page):
            summary = {"filled": 0, "review_required": 0, "paused": 1, "skipped": 0}
            record_autofill_pause(
                application,
                session,
                pause_reason="access_limited_or_bot_blocked",
                field_label="Application page access",
            )
            if keep_open:
                print(f"Access limited. Keeping browser open for {keep_open_seconds} seconds...")
                time.sleep(keep_open_seconds)
            browser.close()
            return summary
        if _is_captcha_page(page):
            print(
                "Paused: captcha_or_bot_verification. "
                f"Please complete verification manually within {captcha_wait_seconds} seconds..."
            )
            if not _wait_for_captcha_clear(page, captcha_wait_seconds, captcha_poll_seconds):
                summary = {"filled": 0, "review_required": 0, "paused": 1, "skipped": 0}
                record_autofill_pause(
                    application,
                    session,
                    pause_reason="captcha_or_bot_verification",
                )
                if keep_open:
                    print(f"Verification still present. Keeping browser open for {keep_open_seconds} seconds...")
                    time.sleep(keep_open_seconds)
                browser.close()
                return summary

        if not _wait_for_form_ready(page, form_wait_seconds, form_poll_seconds):
            pause_reason = (
                "access_limited_or_bot_blocked"
                if _is_access_limited_page(page)
                else "form_not_ready_or_still_loading"
            )
            summary = {"filled": 0, "review_required": 0, "paused": 1, "skipped": 0}
            record_autofill_pause(
                application,
                session,
                pause_reason=pause_reason,
                field_label="Application form",
            )
            if keep_open:
                print(f"Form not ready. Keeping browser open for {keep_open_seconds} seconds...")
                time.sleep(keep_open_seconds)
            browser.close()
            return summary

        raw_fields = page.evaluate(FIELD_DETECTION_SCRIPT)
        fields = [FormField(**item) for item in raw_fields]
        plan = build_autofill_plan(fields, config)

        for item in plan:
            if item.action != "fill":
                continue
            locator = page.locator(item.field.selector).first
            if item.field.field_type in {"checkbox", "radio"}:
                if item.value.lower() in {"yes", "true"}:
                    locator.check()
            else:
                locator.fill(item.value)
            if item.review_required:
                page.locator(item.field.selector).evaluate(
                    "el => { el.style.outline = '3px solid #f59e0b'; el.dataset.reviewRequired = 'true'; }"
                )

        record_autofill_plan(application, plan, session, mark_completed=True)
        summary = summarise_plan(plan)
        if keep_open:
            print(f"Autofill complete. Keeping browser open for {keep_open_seconds} seconds...")
            time.sleep(keep_open_seconds)
        browser.close()
        return summary


def _is_captcha_page(page) -> bool:
    try:
        return bool(page.evaluate(CAPTCHA_DETECTION_SCRIPT))
    except Exception:
        return False


def _is_access_limited_page(page) -> bool:
    try:
        return bool(page.evaluate(ACCESS_LIMIT_DETECTION_SCRIPT))
    except Exception:
        return False


def _wait_for_captcha_clear(page, timeout_seconds: int, poll_seconds: int) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _is_captcha_page(page):
            page.wait_for_load_state("domcontentloaded")
            return True
        time.sleep(poll_seconds)
    return not _is_captcha_page(page)


def _wait_for_form_ready(page, timeout_seconds: int, poll_seconds: int) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        _wait_for_network_quiet(page)
        if _is_access_limited_page(page):
            return False
        if _field_count(page) > 0:
            return True
        time.sleep(poll_seconds)
    return _field_count(page) > 0


def _field_count(page) -> int:
    try:
        return int(page.locator("input, textarea, select").count())
    except Exception:
        return 0


def _wait_for_network_quiet(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
