from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from services.github_service import fetch_contribution_stats

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "🚀 Git Contribution Tracker is running! Add /<username> to see stats."

@app.get("/{username}", response_class=PlainTextResponse)
async def get_stats(username: str):
    stats = await fetch_contribution_stats(username)
    
    if stats["last_day"].startswith("Error"):
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {username}")

    return f"""## {username}'s contributions
- Total contributions (last 30 days): {stats['total_contributions']}
- Current streak: {stats['streak']} days
- Last active day: {stats['last_day']}"""