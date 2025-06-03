import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS server_configs (
    guild_id TEXT PRIMARY KEY,
    youtube TEXT,
    twitch TEXT,
    tiktok TEXT,
    channel_id TEXT
)
""")
conn.commit()
conn.close()

print("✅ Table 'server_configs' créée avec succès.")
