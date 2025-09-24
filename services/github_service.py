import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

async def fetch_contribution_stats(username: str):
    """
    Fetch contributions from GitHub contribution graph (last 30 days).
    """
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
        except httpx.RequestError:
            return {
                "username": username,
                "total_contributions": 0,
                "streak": 0,
                "last_day": "Connection error",
            }

    if response.status_code != 200:
        return {
            "username": username,
            "total_contributions": 0,
            "streak": 0,
            "last_day": f"Error {response.status_code}",
        }

    # Debug: Save HTML for inspection
    with open("debug_github.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Try different selectors for GitHub's contribution graph
    contributions = []
    
    # Method 1: Look for tooltips or contribution data
    tooltips = soup.find_all("tool-tip") or soup.find_all("span", class_=re.compile("tooltip"))
    
    # Method 2: Look for JavaScript data
    script_tags = soup.find_all("script")
    for script in script_tags:
        if "contributionCalendar" in script.text:
            # Extract JSON data from script
            import json
            try:
                # This is a simplified extraction - you might need to adjust
                data_match = re.search(r'var data = (\[.*?\]);', script.text)
                if data_match:
                    contributions_data = json.loads(data_match.group(1))
                    print("DEBUG: Found contributions in script:", contributions_data[:5])
            except:
                pass

    # Method 3: Parse SVG rectangles (your original approach, improved)
    rects = soup.find_all("rect")
    contributions = []
    
    for rect in rects:
        date_str = rect.get("data-date")
        count_str = rect.get("data-count")
        
        # Alternative count extraction from aria-label
        aria_label = rect.get("aria-label", "")
        if not count_str and aria_label:
            # Extract number from "X contributions on date"
            count_match = re.search(r'(\d+)\s+contribution', aria_label)
            if count_match:
                count_str = count_match.group(1)
        
        if date_str and count_str:
            try:
                count = int(count_str)
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                contributions.append({"date": date, "count": count})
            except ValueError:
                continue

    print(f"DEBUG: Found {len(contributions)} contribution days")
    print("DEBUG: Sample contributions:", contributions[:5])

    # If no contributions found, try alternative parsing
    if not contributions:
        # Look for any data attributes
        all_elements = soup.find_all(attrs={"data-date": True})
        for elem in all_elements:
            date_str = elem.get("data-date")
            # Try to find count in various attributes
            for attr_name in ["data-count", "data-level", "data-contributions"]:
                count_str = elem.get(attr_name)
                if count_str:
                    try:
                        count = int(count_str)
                        date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        contributions.append({"date": date, "count": count})
                        break
                    except ValueError:
                        continue

    # Calculate stats for last 30 days
    now = datetime.utcnow().date()
    last_30_days = now - timedelta(days=30)
    
    recent_contributions = [
        c for c in contributions 
        if c["date"] >= last_30_days and c["date"] <= now
    ]
    
    total = sum(c["count"] for c in recent_contributions)
    active_dates = {c["date"] for c in recent_contributions if c["count"] > 0}
    
    # Find last active day
    last_active = None
    if active_dates:
        last_active = max(active_dates)
    
    # Calculate streak
    streak = 0
    current_date = now
    while current_date in active_dates:
        streak += 1
        current_date -= timedelta(days=1)

    print(f"DEBUG: Last 30 days stats - total: {total}, streak: {streak}, last_active: {last_active}")

    return {
        "username": username,
        "total_contributions": total,
        "streak": streak,
        "last_day": last_active.strftime("%Y-%m-%d") if last_active else "N/A",
    }