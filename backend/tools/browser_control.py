import logging
import asyncio
from playwright.async_api import async_playwright

logger = logging.getLogger("AI-OS-BROWSER")

async def execute_browser_task(prompt: str) -> str:
    """
    Parses a user instruction, spins up a physical Chromium window,
    performs human-like interactions, and returns an execution report.
    """
    cleaned_prompt = prompt.lower()
    
    # 1. Determine Intent, Target Destination, and Search Parameters
    target_url = "https://www.google.com"
    search_mode = False
    search_query = ""
    status_message = ""

    if "youtube" in cleaned_prompt:
        target_url = "https://www.youtube.com"
        status_message = "Navigating to YouTube Hub..."
        if "search" in cleaned_prompt or "play" in cleaned_prompt:
            search_mode = True
            # Simple parsing token extraction
            search_query = prompt.split("search")[-1].replace("about", "").replace("for", "").strip() if "search" in prompt else prompt.split("play")[-1].strip()
    elif "linkedin" in cleaned_prompt:
        target_url = "https://www.linkedin.com"
        status_message = "Accessing LinkedIn Portal..."
    elif "google" in cleaned_prompt or "search" in cleaned_prompt:
        target_url = "https://www.google.com"
        status_message = "Opening Google Search Core..."
        search_mode = True
        search_query = prompt.split("search")[-1].replace("about", "").replace("for", "").strip()

    # 2. Launch the Automation Pipeline
    async with async_playwright() as p:
        logger.info("Launching visible browser instance...")
        # headless=False guarantees the browser physically pops up on your laptop screen!
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        
        # Create a clean context and page viewport
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        
        logger.info(f"Navigating to: {target_url}")
        await page.goto(target_url, wait_until="load")
        
        # 3. Perform Interactions Based on State
        if search_mode and search_query:
            logger.info(f"Executing search interaction for: {search_query}")
            if "google" in target_url:
                # Wait for Google search input element, click, type, and press Enter
                await page.wait_for_selector("textarea[name='q']", timeout=5000)
                await page.fill("textarea[name='q']", search_query)
                await page.press("textarea[name='q']", "Enter")
                status_message = f"Successfully searched Google for: '{search_query}'"
            
            elif "youtube" in target_url:
                # Wait for YouTube search bar element
                await page.wait_for_selector("input[name='search_query']", timeout=5000)
                await page.fill("input[name='search_query']", search_query)
                await page.press("input[name='search_query']", "Enter")
                status_message = f"Successfully launched YouTube search sequence for: '{search_query}'"
                
            # Allow page animations and results to populate before snapshotting
            await asyncio.sleep(5)
        else:
            # General navigation hold so the user can verify the window opened successfully
            await asyncio.sleep(4)
            status_message = f"Successfully opened desktop environment terminal and accessed {target_url}"

        # Capture page metadata to report back to Core
        page_title = await page.title()
        await browser.close()
        
        return f"{status_message} (Verified Page Header: '{page_title}')"