import discord
from discord.ext import tasks, commands
import sqlite3
import asyncio
import os
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATABASE = "db.sqlite3"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_TOKEN = None

def get_config(guild_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT youtube, twitch, tiktok, channel_id FROM server_configs WHERE guild_id = ?", (str(guild_id),))
        row = cursor.fetchone()
        if row:
            return {
                "youtube": row[0],
                "twitch": row[1],
                "tiktok": row[2],
                "channel_id": int(row[3]) if row[3] else None
            }
        return None

def is_youtube_live(channel_id):
    if not YOUTUBE_API_KEY or not channel_id:
        return False
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "eventType": "live",
        "type": "video",
        "key": YOUTUBE_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return len(data.get("items", [])) > 0
    except Exception as e:
        print(f"[YouTube] Erreur : {e}")
        return False

def get_twitch_token():
    global TWITCH_TOKEN
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        r.raise_for_status()
        TWITCH_TOKEN = r.json()["access_token"]
    except Exception as e:
        print(f"[Twitch] Erreur d’authentification : {e}")
        TWITCH_TOKEN = None

def is_twitch_live(username):
    global TWITCH_TOKEN
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET or not username:
        return False
    if not TWITCH_TOKEN:
        get_twitch_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_TOKEN}"
    }
    try:
        response = requests.get(f"https://api.twitch.tv/helix/streams?user_login={username}", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return len(data.get("data", [])) > 0
    except Exception as e:
        print(f"[Twitch] Erreur API : {e}")
        return False

def is_tiktok_live(username):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.tiktok.com/@{username}/live"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
        soup = BeautifulSoup(response.text, "html.parser")
        return "LIVE" in soup.text.upper()
    except Exception as e:
        print(f"[TikTok] Erreur : {e}")
        return False

@bot.event
async def on_ready():
    print(f"✅ Bot prêt : {bot.user}")
    check_streams.start()

@tasks.loop(seconds=60)
async def check_streams():
    print("🔄 Vérification des serveurs configurés...")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT guild_id, youtube, twitch, tiktok, channel_id FROM server_configs")
        for row in cursor.fetchall():
            guild_id, youtube, twitch, tiktok, channel_id = row
            if not channel_id:
                continue
            guild = bot.get_guild(int(guild_id))
            if not guild:
                continue
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            alerts = []
            if youtube and is_youtube_live(youtube):
                alerts.append(f"🔴 **LIVE YouTube détecté** sur `{youtube}`")
            if twitch and is_twitch_live(twitch):
                alerts.append(f"🟣 **LIVE Twitch détecté** sur `{twitch}`")
            if tiktok and is_tiktok_live(tiktok):
                alerts.append(f"🎥 **LIVE TikTok détecté** sur `{tiktok}`")

            for alert in alerts:
                await channel.send(alert)

@bot.command()
async def config(ctx):
    conf = get_config(ctx.guild.id)
    if conf:
        msg = (
            f"🎯 Config du serveur :\n"
            f"📺 YouTube: `{conf['youtube']}`\n"
            f"🟣 Twitch: `{conf['twitch']}`\n"
            f"🎥 TikTok: `{conf['tiktok']}`\n"
            f"💬 Salon ID: `{conf['channel_id']}`"
        )
        await ctx.send(msg)
    else:
        await ctx.send("❌ Aucune configuration trouvée pour ce serveur.")

# Démarrage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ DISCORD_TOKEN manquant dans .env")
