import discord
from discord.ext import commands
import os
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ============ DATA ============
users_db = {}

WEAPONS = {
    "mp5": {"dmg": 35, "range": 15, "fire_rate": 900, "mag": 30, "rarity": "common"},
    "ak74": {"dmg": 48, "range": 45, "fire_rate": 650, "mag": 30, "rarity": "common"},
    "grau": {"dmg": 40, "range": 60, "fire_rate": 750, "mag": 36, "rarity": "rare"},
    "m13": {"dmg": 38, "range": 55, "fire_rate": 850, "mag": 30, "rarity": "rare"},
    "ak47": {"dmg": 60, "range": 50, "fire_rate": 600, "mag": 30, "rarity": "epic"},
    "holger": {"dmg": 52, "range": 40, "fire_rate": 700, "mag": 100, "rarity": "epic"},
    "ram7": {"dmg": 45, "range": 35, "fire_rate": 900, "mag": 45, "rarity": "rare"},
    "vanguard": {"dmg": 80, "range": 70, "fire_rate": 500, "mag": 20, "rarity": "legendary"},
}

OPERATORS = {
    "ghost": {"rarity": "legendary", "cost": 2400, "desc": "Tier 1 Operator"},
    "roze": {"rarity": "legendary", "cost": 2400, "desc": "Shadow Company"},
    "soap": {"rarity": "epic", "cost": 1200, "desc": "SAS Legend"},
    "gaz": {"rarity": "epic", "cost": 1200, "desc": "141 Assault"},
    "farah": {"rarity": "epic", "cost": 1200, "desc": "Urzikstan Freedom"},
    "konig": {"rarity": "legendary", "cost": 2400, "desc": "KorTac Titan"},
    "nikto": {"rarity": "legendary", "cost": 2400, "desc": "Chimera Merc"},
    "otter": {"rarity": "rare", "cost": 600, "desc": "Chimera Operator"},
}

class Player:
    def __init__(self, uid):
        self.id, self.level, self.prestige, self.xp = uid, 1, 0, 0
        self.cod_points, self.balance = 0, 0
        self.kills, self.deaths, self.wins, self.matches, self.headshots = 0, 0, 0, 0, 0
        self.operator_skin, self.purchased_skins, self.weapons = "default", ["default"], list(WEAPONS.keys())[:3]
        self.ranked_tier, self.rank_points, self.clan_tag, self.last_daily = "Bronze", 0, "", None
        self.win_streak, self.best_streak = 0, 0

def get_player(uid):
    return users_db.setdefault(uid, Player(uid))

def calc_kd(k, d):
    return round(k / max(d, 1), 2)

# ============ EVENTS ============
@bot.event
async def on_ready():
    print(f"✅ {bot.user} online - tactical systems active")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Modern Warfare"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help`")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`")
    else:
        await ctx.send(f"❌ Error: {str(error)[:100]}")

# ============ PROFILE COMMANDS ============
@bot.command(name="profile", aliases=["p", "stats"])
async def profile(ctx, user=None):
    """View your or another player's profile"""
    target = bot.get_user(int(user)) if user and user.isdigit() else ctx.author
    p = get_player(target.id)
    kd = calc_kd(p.kills, p.deaths)
    
    embed = discord.Embed(title=f"[{p.clan_tag}] {target.name}", description=f"**{p.ranked_tier}** | Prestige {p.prestige}", color=discord.Color.from_rgb(255, 65, 0))
    embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
    embed.add_field(name="🎯 Combat", value=f"**K/D:** {kd}\n**Kills:** {p.kills:,}\n**Deaths:** {p.deaths:,}", inline=True)
    embed.add_field(name="📊 Progression", value=f"**Level:** {p.level}\n**XP:** {p.xp:,}\n**Matches:** {p.matches}", inline=True)
    embed.add_field(name="🏆 Ranked", value=f"**Tier:** {p.ranked_tier}\n**Win Rate:** {round(p.wins / max(p.matches, 1) * 100, 1)}%\n**Streak:** {p.win_streak}", inline=True)
    embed.add_field(name="💰 Economy", value=f"**CP:** {p.cod_points:,}\n**Balance:** ${p.balance:,}", inline=True)
    await ctx.send(embed=embed)

# ============ ECONOMY COMMANDS ============
@bot.command(name="daily")
async def daily(ctx):
    """Claim daily rewards"""
    p = get_player(ctx.author.id)
    now = datetime.now()
    if p.last_daily and (now - p.last_daily).total_seconds() < 86400:
        h = int((86400 - (now - p.last_daily).total_seconds()) // 3600)
        await ctx.send(f"⏰ Already claimed. Back in {h}h")
        return
    
    cp, cash = random.randint(100, 500), random.randint(1000, 5000)
    if p.win_streak >= 5:
        cp, cash = int(cp * 1.5), int(cash * 1.5)
        bonus = "🔥 WIN STREAK BONUS"
    else:
        bonus = ""
    
    p.cod_points, p.balance, p.last_daily = p.cod_points + cp, p.balance + cash, now
    embed = discord.Embed(title="📦 Daily Rewards", color=discord.Color.gold())
    embed.add_field(name="COD Points", value=f"+{cp}", inline=True)
    embed.add_field(name="Cash", value=f"+${cash:,}", inline=True)
    if bonus:
        embed.add_field(name="Bonus", value=bonus, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="shop")
async def shop(ctx, cat="operators"):
    """Browse store"""
    if cat == "operators":
        embed = discord.Embed(title="🎭 Operator Store", color=discord.Color.from_rgb(255, 0, 128))
        for name, data in OPERATORS.items():
            embed.add_field(name=f"{name.upper()} [{data['rarity']}]", value=f"{data['desc']}\n💳 ${data['cost']}", inline=True)
    elif cat == "weapons":
        embed = discord.Embed(title="🔫 Weapon Store", color=discord.Color.from_rgb(200, 0, 0))
        for w, s in WEAPONS.items():
            embed.add_field(name=w.upper(), value=f"DMG: {s['dmg']} | Range: {s['range']} | ROF: {s['fire_rate']}\n[{s['rarity']}]", inline=True)
    else:
        embed = discord.Embed(title="❌ Not found", color=discord.Color.red())
    embed.set_footer(text="Use !buy <item> | !shop <operators/weapons>")
    await ctx.send(embed=embed)

@bot.command(name="buy")
async def buy(ctx, item):
    """Purchase item"""
    p = get_player(ctx.author.id)
    item = item.lower()
    
    if item in OPERATORS:
        cost = OPERATORS[item]["cost"]
        if p.cod_points < cost:
            await ctx.send(f"❌ Need {cost - p.cod_points} more CP")
            return
        p.cod_points -= cost
        p.purchased_skins.append(item)
        p.operator_skin = item
        embed = discord.Embed(title="✅ Purchase Complete", description=f"Unlocked **{item.upper()}**", color=discord.Color.green())
    else:
        await ctx.send("❌ Item not found")
        return
    await ctx.send(embed=embed)

# ============ COMBAT COMMANDS ============
@bot.command(name="match", aliases=["m"])
async def match(ctx, mode="tdm"):
    """Start ranked match"""
    modes = ["tdm", "snd", "domination", "hardpoint", "ffa", "warzone"]
    if mode.lower() not in modes:
        await ctx.send(f"❌ Available: {', '.join(modes)}")
        return
    
    p = get_player(ctx.author.id)
    k, d, a, hs = random.randint(5, 35), random.randint(3, 20), random.randint(2, 10), random.randint(0, 10)
    won = random.choice([True, False])
    
    p.kills, p.deaths, p.matches, p.headshots = p.kills + k, p.deaths + d, p.matches + 1, p.headshots + hs
    xp = (k * 50) + (d * -10) + (a * 25)
    p.xp += xp
    
    if won:
        p.wins, p.win_streak, p.balance = p.wins + 1, p.win_streak + 1, p.balance + random.randint(500, 2000)
        p.best_streak = max(p.best_streak, p.win_streak)
        result, color = "🔥 VICTORY", discord.Color.green()
    else:
        p.win_streak, p.balance = 0, p.balance + random.randint(100, 500)
        result, color = "❌ DEFEAT", discord.Color.red()
    
    lvl_up = ""
    if p.xp >= p.level * 1000:
        p.level, p.xp = p.level + 1, 0
        lvl_up = f"\n⬆️ **LEVEL {p.level}**"
    
    embed = discord.Embed(title=f"{result} - {mode.upper()}", color=color)
    embed.add_field(name="📊 Stats", value=f"**K/D/A:** {k}/{d}/{a}\n**Headshots:** {hs}\n**XP:** +{xp}{lvl_up}", inline=True)
    embed.add_field(name="💰 Rewards", value=f"**Streak:** {p.win_streak}", inline=True)
    embed.set_footer(text=f"K/D: {calc_kd(p.kills, p.deaths)}")
    await ctx.send(embed=embed)

@bot.command(name="loadout")
async def loadout(ctx, weapon=None):
    """Manage loadout"""
    p = get_player(ctx.author.id)
    
    if weapon:
        weapon = weapon.lower()
        if weapon not in WEAPONS:
            await ctx.send(f"❌ Not found. Available: {', '.join(WEAPONS.keys())}")
            return
        if weapon not in p.weapons:
            await ctx.send("❌ You don't own this")
            return
        p.weapons[0] = weapon
        await ctx.send(f"✅ Equipped: **{weapon.upper()}**")
        return
    
    embed = discord.Embed(title="⚙️ Your Loadout", color=discord.Color.blue())
    for i, w in enumerate(p.weapons, 1):
        if w in WEAPONS:
            s = WEAPONS[w]
            embed.add_field(name=f"Slot {i}: {w.upper()}", value=f"DMG: {s['dmg']} | Range: {s['range']} | ROF: {s['fire_rate']}", inline=False)
    embed.set_footer(text="Use !loadout <weapon> to equip")
    await ctx.send(embed=embed)

# ============ LEADERBOARD COMMANDS ============
@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx, stat="kills"):
    """View leaderboards"""
    stats = {
        "kills": lambda p: p.kills,
        "level": lambda p: p.level,
        "wins": lambda p: p.wins,
        "kd": lambda p: calc_kd(p.kills, p.deaths),
        "matches": lambda p: p.matches,
    }
    
    if stat not in stats:
        await ctx.send(f"❌ Available: {', '.join(stats.keys())}")
        return
    
    top = sorted(users_db.items(), key=lambda x: stats[stat](x[1]), reverse=True)[:15]
    embed = discord.Embed(title=f"🏆 {stat.upper()} Leaderboard", color=discord.Color.gold())
    medals = ["🥇", "🥈", "🥉"]
    
    for rank, (uid, player) in enumerate(top, 1):
        medal = medals[rank - 1] if rank <= 3 else f"{rank}."
        val = stats[stat](player)
        if stat != "kd":
            val = f"{val:,}"
        embed.add_field(name=f"{medal} <@{uid}>", value=f"**{val}** | Lvl {player.level}", inline=False)
    
    await ctx.send(embed=embed)

# ============ INFO COMMANDS ============
@bot.command(name="init")
async def init(ctx):
    """Initialize account"""
    p = get_player(ctx.author.id)
    p.cod_points, p.balance = 500, 5000
    
    embed = discord.Embed(title="✅ Account Initialized", description="Welcome to Modern Warfare", color=discord.Color.green())
    embed.add_field(name="Starting CP", value="500", inline=True)
    embed.add_field(name="Starting Cash", value="$5,000", inline=True)
    embed.add_field(name="Weapons", value="MP5, AK74, M13", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["commands"])
async def help_cmd(ctx):
    """Command list"""
    embed = discord.Embed(title="🎮 Modern Warfare Bot Commands", color=discord.Color.from_rgb(255, 65, 0))
    
    cmds = {
        "👤 Profile": ["`!profile` - View stats", "`!init` - Initialize account"],
        "💰 Economy": ["`!daily` - Daily rewards", "`!shop [operators/weapons]` - Browse", "`!buy <item>` - Purchase"],
        "🎮 Combat": ["`!match [mode]` - Start match", "`!loadout [weapon]` - Manage loadout"],
        "🏆 Competitive": ["`!leaderboard [stat]` - Rankings"],
    }
    
    for cat, lst in cmds.items():
        embed.add_field(name=cat, value="\n".join(lst), inline=False)
    
    await ctx.send(embed=embed)

# ============ RUN ============
if __name__ == "__main__":
    bot.run(TOKEN)
