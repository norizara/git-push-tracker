from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from services.github_service import fetch_contribution_stats
import os

app = FastAPI()

# Get port from Railway environment variable
port = int(os.environ.get("PORT", 8000))

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "🚀 Git Contribution Tracker is running! Add /<username> to see stats."

@app.get("/{username}", response_class=PlainTextResponse)
async def get_stats(username: str):
    try:
        stats = await fetch_contribution_stats(username)
        
        if stats["last_day"].startswith("Error"):
            return f"Error: Could not fetch data for {username}"
        
        return f"""## {username}'s contributions
- Total contributions (last 30 days): {stats['total_contributions']}
- Current streak: {stats['streak']} days
- Last active day: {stats['last_day']}"""
    
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))  # Use Railway's PORT or default to 8080
    uvicorn.run(app, host="0.0.0.0", port=port)