# Modern Warfare Discord Bot

Lean, fast CoD-themed bot. Ranked matches, cosmetics, economy, leaderboards.

## 📦 Files
- `main.py` - Complete bot (all commands & data)
- `requirements.txt` - Dependencies
- `.env.example` - Config template

## 🚀 Deploy

### Railway
1. Push to GitHub
2. Connect to Railway
3. Set env var: `DISCORD_TOKEN=your_token`

### Local
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your token to .env
python main.py
```

## 🎮 Commands
- `!profile` - Stats
- `!daily` - Rewards
- `!shop [operators/weapons]` - Store
- `!buy <item>` - Purchase
- `!match [mode]` - Play
- `!loadout [weapon]` - Equip
- `!leaderboard [stat]` - Rankings
- `!help` - Commands

## 🔫 Weapons
MP5, AK74, Grau, M13, AK47, Holger, RAM7, Vanguard

## 🎭 Operators
Ghost, Roze, Soap, Gaz, Farah, König, Nikto, Otter

---

Ready to deploy. No fluff.
