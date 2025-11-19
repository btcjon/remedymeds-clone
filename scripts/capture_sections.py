"""Capture RemedyMeds landing page sections as standalone screenshots."""
from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright, Page

URL = "https://remedymeds.com/"
MIN_SECTION_HEIGHT = 200
MIN_SECTION_WIDTH = 400
MAX_SECTIONS = 10


async def dismiss_banners(page: Page) -> None:
    """Dismiss common modal / banner buttons if they appear."""
    selectors = [
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I Accept')",
        "button:has-text('I Agree')",
        "button:has-text('Agree')",
        "button:has-text('Got it')",
        "button:has-text('Close')",
        "button:has-text('Continue without')",
        "button:has-text('No thanks')",
        "[aria-label='Close']",
    ]
    for selector in selectors:
        try:
            button = page.locator(selector).first
            if await button.count():
                await button.click(timeout=1500)
                await page.wait_for_timeout(500)
        except Exception:
            continue


async def capture_sections() -> int:
    output_dir = Path(__file__).resolve().parent.parent / "sections"
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5,
        )
        await page.goto(URL, wait_until="networkidle")
        await dismiss_banners(page)
        await page.wait_for_timeout(2000)

        sections = page.locator("main section")
        total = await sections.count()
        saved = 0

        for idx in range(total):
            section = sections.nth(idx)
            box = await section.bounding_box()
            if not box:
                continue
            if box["height"] < MIN_SECTION_HEIGHT or box["width"] < MIN_SECTION_WIDTH:
                continue

            try:
                await section.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                continue

            await page.wait_for_timeout(400)
            target = output_dir / f"section-{saved + 1:02}.png"
            await section.screenshot(path=str(target), type="png")
            saved += 1

            if saved >= MAX_SECTIONS:
                break

        await browser.close()
    return saved


async def main() -> None:
    saved = await capture_sections()
    print(f"Captured {saved} section screenshot(s) into the sections folder.")


if __name__ == "__main__":
    asyncio.run(main())

