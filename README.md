# Modern Warfare Discord Bot

A feature-rich Call of Duty themed Discord bot with ranked matchmaking, economy system, operator cosmetics, and competitive tournaments.

## 🎮 Features

### Combat System
- **Ranked Matches** - Simulate CoD matches with realistic stats (TDM, S&D, Domination, Hardpoint, FFA, Warzone)
- **K/D Tracking** - Track your kill/death ratio, headshots, and match history
- **Loadout Management** - Create and manage weapon loadouts with authentic CoD weapon stats
- **Win Streaks** - Track consecutive wins with bonus rewards

### Economy
- **COD Points** - Premium currency for cosmetics
- **Cash Rewards** - Earn from daily login, matches, and tournaments
- **Dynamic Pricing** - Different rarities and costs for cosmetics

### Cosmetics
- **Operator Skins** - Ghost, Roze, Soap, Gaz, Farah, König, Nikto, Otter (with authentic descriptions)
- **Weapon Arsenal** - Unlock MP5, AK74, Grau, M13, AK47, Holger, RAM7, Vanguard
- **Attachments** - Monolithic Silencer, Snatch Grip, Sleight of Hand, StiPrPled Grip, VLK 3.0x

### Progression
- **Level System** - Prestige ranks with XP progression
- **Ranked Tiers** - Bronze → Legendary with rank points
- **Leaderboards** - Global rankings by kills, K/D, level, wins, matches, prestige

### Competitive
- **Tournaments** - Seasonal ranked competitions with prize pools
- **Clans** - Create and manage clans with custom tags
- **Clan Wars** - Cross-server clan competitions (expandable)

## 🚀 Deployment

### Railway (Recommended)
1. Fork this repository
2. Connect to Railway: https://railway.app
3. Add `DISCORD_TOKEN` environment variable
4. Deploy

### Local Development
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your Discord token to .env
python main.py
```

## 📋 Commands

### Profile
- `!profile [user]` - View stats
- `!stats` - Stats alias
- `!init` - Initialize account

### Economy
- `!daily` - Claim daily rewards
- `!shop [operators/weapons]` - Browse store
- `!buy <item>` - Purchase cosmetics
- `!balance` - Check account balance

### Combat
- `!match [gamemode]` - Start ranked match
- `!loadout [weapon]` - Manage loadout
- `!stats` - View combat stats

### Competitive
- `!leaderboard [stat]` - Global rankings
- `!tournament [info/join/bracket]` - Tournament management
- `!clan [info/create]` - Clan system

### Info
- `!help` - Command list
- `!commands` - Alias for help

## 🛠️ Weapon Stats

Each weapon has configurable:
- Damage (DMG)
- Range
- Fire Rate (ROF)
- Magazine Size
- Rarity (Common/Rare/Epic/Legendary)

Current arsenal includes MP5, AK74, Grau, M13, AK47, Holger, RAM7, Vanguard

## 📊 Database

Currently uses in-memory storage (suitable for testing). For production, integrate PostgreSQL via `DATABASE_URL` environment variable.

## 🔐 Environment Variables

```
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:pass@host/db  # Optional, defaults to SQLite
```

## 📝 License

MIT License

## 🤝 Contributing

Feel free to submit issues and PRs!

---

**Modern Warfare Bot** - Competitive Discord gaming made simple.
