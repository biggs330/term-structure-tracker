"""Run this yourself to actually post to #journalclub. Not run automatically.

Requires DISCORD_WEBHOOK_URL set in a local .env file (see .env.example).
"""

from src.term_structure.config import OUTPUTS
from src.term_structure.notify import post_to_discord

label = (OUTPUTS / "label.txt").read_text().strip()
chart = str(OUTPUTS / "regime_chart.png")
animation = str(OUTPUTS / "curve_animation.gif")

response = post_to_discord(label, file_paths=[animation, chart])
print(f"Posted. Discord response: {response.status_code}")
