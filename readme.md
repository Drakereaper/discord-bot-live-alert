# Discord Bot Live Alert

Un bot Discord avec dashboard web permettant de recevoir des alertes de live YouTube, Twitch et TikTok dans le salon Discord de votre choix.

## Fonctionnalités
- Détection de live YouTube via API officielle
- Détection de live Twitch via Helix API
- Scraping TikTok pour détection simple
- Interface web avec authentification Discord
- Multi-serveur (chaque Discord configure son propre suivi)

## Installation locale

```bash
# Installer les dépendances du bot
pip install -r requirements.txt

# Lancer le bot
python bot.py

# Lancer le dashboard (depuis discord_dashboard_advanced/)
cd discord_dashboard_advanced
pip install -r requirements.txt
python app.py

---

## Auteur

Développé avec ❤️ par [Drakereaper](https://github.com/Drakereaper)

- 💻 Discord : StreamAlert#5255
- 🌐 Projet personnel – alertes multi-plateformes en direct

