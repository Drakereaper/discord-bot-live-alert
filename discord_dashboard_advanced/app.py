import os
from flask import Flask, redirect, request, session, url_for, render_template
import requests
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

# 🔹 Page d'accueil
@app.route('/')
def index():
    return render_template("login.html")

# 🔹 Route appelée par le bouton "Connexion"
@app.route('/login')
def login():
    return redirect(DISCORD_OAUTH_URL)

# 🔹 Redirection après autorisation Discord
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

# 🔹 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    user = session['user']

    guilds = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers={
        'Authorization': f"Bearer {session['access_token']}"
    }).json()

    # On garde uniquement ceux où l'utilisateur est admin (permissions & 0x8)
    guilds = [g for g in guilds_raw if int(g['permissions']) & 0x8]

    return render_template("dashboard.html", user=user, guilds=guilds)

# 🔹 Déconnexion
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 🔹 Gestion serveur
@app.route('/manage/<int:guild_id>')
def manage_server(guild_id):
    if 'user' not in session:
        return redirect('/')
    return render_template("manage.html", guild_id=guild_id)

# 🔹 Démarrage Flask pour Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
