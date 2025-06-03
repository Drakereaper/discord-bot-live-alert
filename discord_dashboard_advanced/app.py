# app.py (extrait mis à jour)

from flask import Flask, redirect, request, session, url_for, render_template
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
API_BASE_URL = "https://discord.com/api/v10"
OAUTH_SCOPE = "identify guilds"
DISCORD_OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={OAUTH_SCOPE.replace(' ', '%20')}"

@app.route('/')
def index():
    return render_template("login.html")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')

    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': OAUTH_SCOPE
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    credentials = r.json()
    session['access_token'] = credentials['access_token']

    user_info = requests.get(f"{API_BASE_URL}/users/@me", headers={
        'Authorization': f"Bearer {session['access_token']}"
    }).json()

    session['user'] = user_info
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    try:
        user = session['user']

        guilds_resp = requests.get(
            f"{API_BASE_URL}/users/@me/guilds",
            headers={
                'Authorization': f"Bearer {session['access_token']}"
            }
        )
        guilds_resp.raise_for_status()
        all_guilds = guilds_resp.json()

        filtered_guilds = [g for g in all_guilds if int(g.get('permissions', 0)) & 0x20]

        return render_template("dashboard.html", user=user, guilds=filtered_guilds)

    except Exception as e:
        print("[ERROR] Dashboard failed:", e)
        return "Erreur interne dans le dashboard.", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/manage/<int:guild_id>')
def manage_server(guild_id):
    if 'user' not in session:
        return redirect('/')
    return render_template("manage.html", guild_id=guild_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
