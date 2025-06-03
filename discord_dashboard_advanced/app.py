import os, sqlite3, requests
from flask import Flask, session, redirect, request, render_template, url_for
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

DATABASE = "db.sqlite3"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS server_configs (
            guild_id TEXT PRIMARY KEY,
            youtube TEXT,
            twitch TEXT,
            tiktok TEXT,
            channel_id TEXT
        )
        """)
init_db()

@app.route("/")
def index():
    if "user" in session:
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/login")
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify guilds"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    token = r.json()["access_token"]
    session["token"] = token

    user_res = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {token}"})
    session["user"] = user_res.json()
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    token = session["token"]
    r = requests.get("https://discord.com/api/users/@me/guilds", headers={"Authorization": f"Bearer {token}"})
    all_guilds = r.json()
    guilds = []
    for g in all_guilds:
        if int(g.get("permissions", 0)) & 0x20:
            g["bot_present"] = g["id"].endswith("2")  # <- À remplacer plus tard par une vraie détection
            guilds.append(g)
    return render_template("dashboard.html", user=session["user"], guilds=guilds, client_id=CLIENT_ID)

@app.route("/manage/<guild_id>", methods=["GET", "POST"])
def manage(guild_id):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        if request.method == "POST":
            youtube = request.form.get("youtube")
            twitch = request.form.get("twitch")
            tiktok = request.form.get("tiktok")
            channel_id = request.form.get("channel_id")
            c.execute("REPLACE INTO server_configs (guild_id, youtube, twitch, tiktok, channel_id) VALUES (?, ?, ?, ?, ?)",
                      (guild_id, youtube, twitch, tiktok, channel_id))
            conn.commit()
        c.execute("SELECT * FROM server_configs WHERE guild_id = ?", (guild_id,))
        row = c.fetchone()
        config = dict(guild_id=guild_id, youtube=None, twitch=None, tiktok=None, channel_id=None)
        if row:
            config.update(dict(zip(["guild_id", "youtube", "twitch", "tiktok", "channel_id"], row)))
    return render_template("manage.html", config=config, guild_name=f"Serveur {guild_id}")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
