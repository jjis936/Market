import discord
from discord.ext import commands, tasks
import json
import random
import os
from datetime import datetime, timedelta
from typing import Optional

# Environment config for Railway
TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///cod_bot.db")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory database (upgrade to PostgreSQL for production)
users_db = {}
lobbies = {}
tournaments = {}
clans = {}

# CoD Weapons Database
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

ATTACHMENTS = {
    "monolithic_silencer": {"dmg_mult": 0.95, "range_add": 10, "stealth": True},
    "snatch_grip": {"handling_add": 15},
    "sleight_of_hand": {"reload_mult": 1.5},
    "stippled_grip": {"aim_stability": 20},
    "vlk_3.0x": {"scope": True, "range_mult": 1.2},
}

OPERATOR_SKINS = {
    "ghost": {"rarity": "legendary", "cost": 2400, "desc": "Tier 1 Operator"},
    "roze": {"rarity": "legendary", "cost": 2400, "desc": "Shadow Company"},
    "soap": {"rarity": "epic", "cost": 1200, "desc": "SAS Legend"},
    "gaz": {"rarity": "epic", "cost": 1200, "desc": "141 Assault"},
    "farah": {"rarity": "epic", "cost": 1200, "desc": "Urzikstan Freedom"},
    "konig": {"rarity": "legendary", "cost": 2400, "desc": "KorTac Titan"},
    "nikto": {"rarity": "legendary", "cost": 2400, "desc": "Chimera Merc"},
    "otter": {"rarity": "rare", "cost": 600, "desc": "Chimera Operator"},
}

class PlayerProfile:
    def __init__(self, user_id):
        self.id = user_id
        self.username = None
        self.level = 1
        self.prestige = 0
        self.xp = 0
        self.cod_points = 0
        self.balance = 0
        
        # Combat stats
        self.kills = 0
        self.deaths = 0
        self.kd_ratio = 0.0
        self.wins = 0
        self.matches = 0
        self.headshots = 0
        
        # Equipment
        self.loadouts = {}
        self.operator_skin = "default"
        self.purchased_skins = ["default"]
        self.weapons = list(WEAPONS.keys())[:3]
        
        # Progression
        self.ranked_tier = "Bronze"
        self.rank_points = 0
        self.season_stats = {}
        
        # Meta
        self.clan_id = None
        self.last_match = None
        self.banner = "default"
        self.clan_tag = ""
        
        # Economy
        self.last_daily = None
        self.win_streak = 0
        self.best_streak = 0

def get_player(user_id):
    if user_id not in users_db:
        users_db[user_id] = PlayerProfile(user_id)
    return users_db[user_id]

def calculate_kd(kills, deaths):
    return round(kills / max(deaths, 1), 2)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} deployed. tactical systems online.")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="Modern Warfare")
    )

# ============== PROFILE COMMANDS ==============

@bot.command(name="profile", aliases=["p", "stats"])
async def profile(ctx, user: Optional[discord.User] = None):
    """View your or another player's profile"""
    target = user or ctx.author
    player = get_player(target.id)
    
    kd = calculate_kd(player.kills, player.deaths)
    embed = discord.Embed(
        title=f"[{player.clan_tag}] {target.name}",
        description=f"**{player.ranked_tier}** | Prestige {player.prestige}",
        color=discord.Color.from_rgb(255, 65, 0),
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
    
    # Stats
    embed.add_field(
        name="🎯 Combat",
        value=f"**K/D:** {kd}\n**Kills:** {player.kills:,}\n**Deaths:** {player.deaths:,}",
        inline=True
    )
    embed.add_field(
        name="📊 Progression",
        value=f"**Level:** {player.level}\n**XP:** {player.xp:,}\n**Matches:** {player.matches}",
        inline=True
    )
    embed.add_field(
        name="🏆 Ranked",
        value=f"**Tier:** {player.ranked_tier}\n**Win Rate:** {round(player.wins / max(player.matches, 1) * 100, 1)}%\n**Streak:** {player.win_streak}",
        inline=True
    )
    
    embed.add_field(
        name="💰 Economy",
        value=f"**CP:** {player.cod_points:,}\n**Balance:** ${player.balance:,}",
        inline=True
    )
    embed.add_field(
        name="🎮 Loadout",
        value=f"**Operator:** {player.operator_skin}\n**Primary:** {player.weapons[0] if player.weapons else 'None'}",
        inline=True
    )
    embed.add_field(
        name="👥 Clan",
        value=player.clan_tag if player.clan_tag else "None",
        inline=True
    )
    
    await ctx.send(embed=embed)

# ============== ECONOMY COMMANDS ==============

@bot.command(name="daily")
async def daily_reward(ctx):
    """Claim your daily COD Points and cash"""
    player = get_player(ctx.author.id)
    now = datetime.now()
    
    if player.last_daily and (now - player.last_daily).total_seconds() < 86400:
        remaining = 86400 - (now - player.last_daily).total_seconds()
        hours = int(remaining // 3600)
        await ctx.send(f"⏰ Daily already claimed. Back in {hours}h")
        return
    
    cp_reward = random.randint(100, 500)
    cash_reward = random.randint(1000, 5000)
    
    if player.win_streak >= 5:
        cp_reward = int(cp_reward * 1.5)
        cash_reward = int(cash_reward * 1.5)
        streak_bonus = "🔥 WIN STREAK BONUS APPLIED"
    else:
        streak_bonus = ""
    
    player.cod_points += cp_reward
    player.balance += cash_reward
    player.last_daily = now
    
    embed = discord.Embed(
        title="📦 Daily Rewards Claimed",
        color=discord.Color.gold()
    )
    embed.add_field(name="COD Points", value=f"+{cp_reward}", inline=True)
    embed.add_field(name="Cash", value=f"+${cash_reward:,}", inline=True)
    if streak_bonus:
        embed.add_field(name="Bonus", value=streak_bonus, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="shop")
async def shop(ctx, category: str = "operators"):
    """Browse the store"""
    category = category.lower()
    
    if category == "operators":
        embed = discord.Embed(
            title="🎭 Operator Store",
            description="Premium cosmetics",
            color=discord.Color.from_rgb(255, 0, 128)
        )
        for name, data in OPERATOR_SKINS.items():
            embed.add_field(
                name=f"{name.upper()} [{data['rarity']}]",
                value=f"{data['desc']}\n💳 ${data['cost']}",
                inline=True
            )
    
    elif category == "weapons":
        embed = discord.Embed(
            title="🔫 Weapon Store",
            description="Unlock new arsenals",
            color=discord.Color.from_rgb(200, 0, 0)
        )
        for weapon, stats in WEAPONS.items():
            embed.add_field(
                name=weapon.upper(),
                value=f"DMG: {stats['dmg']} | Range: {stats['range']} | ROF: {stats['fire_rate']}\n[{stats['rarity']}]",
                inline=True
            )
    
    embed.set_footer(text="Use !buy <item> to purchase | !shop <operators/weapons>")
    await ctx.send(embed=embed)

@bot.command(name="buy")
async def purchase(ctx, item: str):
    """Purchase an operator or weapon"""
    player = get_player(ctx.author.id)
    item = item.lower()
    
    if item in OPERATOR_SKINS:
        cost = OPERATOR_SKINS[item]["cost"]
        if player.cod_points < cost:
            await ctx.send(f"❌ Need {cost - player.cod_points} more COD Points")
            return
        
        player.cod_points -= cost
        player.purchased_skins.append(item)
        player.operator_skin = item
        
        embed = discord.Embed(
            title="✅ Purchase Complete",
            description=f"Unlocked **{item.upper()}**",
            color=discord.Color.green()
        )
    else:
        await ctx.send("❌ Item not found")
        return
    
    await ctx.send(embed=embed)

# ============== COMBAT COMMANDS ==============

@bot.command(name="match", aliases=["m"])
async def start_match(ctx, gamemode: str = "tdm"):
    """Start a ranked match"""
    gamemodes = ["tdm", "snd", "domination", "hardpoint", "ffa", "warzone"]
    gamemode = gamemode.lower()
    
    if gamemode not in gamemodes:
        await ctx.send(f"❌ Gamemode not found. Available: {', '.join(gamemodes)}")
        return
    
    player = get_player(ctx.author.id)
    
    # Simulate match
    kills = random.randint(5, 35)
    deaths = random.randint(3, 20)
    assists = random.randint(2, 10)
    headshots = random.randint(0, kills // 2)
    
    # Win or loss
    won = random.choice([True, False])
    
    # Update stats
    player.kills += kills
    player.deaths += deaths
    player.matches += 1
    player.headshots += headshots
    
    xp_gained = (kills * 50) + (deaths * -10) + (assists * 25)
    player.xp += xp_gained
    
    if won:
        player.wins += 1
        player.win_streak += 1
        player.balance += random.randint(500, 2000)
        
        if player.win_streak > player.best_streak:
            player.best_streak = player.win_streak
        
        result_text = "🔥 VICTORY"
        result_color = discord.Color.green()
    else:
        player.win_streak = 0
        player.balance += random.randint(100, 500)
        
        result_text = "❌ DEFEAT"
        result_color = discord.Color.red()
    
    # Level up check
    level_up = False
    if player.xp >= player.level * 1000:
        player.level += 1
        player.xp = 0
        level_up = True
    
    embed = discord.Embed(
        title=f"{result_text} - {gamemode.upper()}",
        color=result_color,
        timestamp=datetime.now()
    )
    embed.add_field(name="📊 Match Stats", value=f"**K/D/A:** {kills}/{deaths}/{assists}\n**Headshots:** {headshots}\n**XP:** +{xp_gained}", inline=True)
    embed.add_field(name="💰 Rewards", value=f"**Cash:** +${random.randint(500, 2000)}\n**Streak:** {player.win_streak}", inline=True)
    
    if level_up:
        embed.add_field(name="⬆️ LEVEL UP", value=f"You reached **Level {player.level}**!", inline=False)
    
    embed.set_footer(text=f"Overall K/D: {calculate_kd(player.kills, player.deaths)}")
    await ctx.send(embed=embed)

@bot.command(name="loadout")
async def loadout(ctx, weapon: str = None):
    """View or set your loadout"""
    player = get_player(ctx.author.id)
    
    if weapon:
        weapon = weapon.lower()
        if weapon not in WEAPONS:
            await ctx.send(f"❌ Weapon not found. Available: {', '.join(WEAPONS.keys())}")
            return
        
        if weapon not in player.weapons:
            await ctx.send(f"❌ You don't own this weapon yet")
            return
        
        player.weapons[0] = weapon
        await ctx.send(f"✅ Loadout updated: **{weapon.upper()}**")
        return
    
    embed = discord.Embed(
        title="⚙️ Your Loadout",
        color=discord.Color.blue()
    )
    
    for i, weap in enumerate(player.weapons, 1):
        if weap in WEAPONS:
            stats = WEAPONS[weap]
            embed.add_field(
                name=f"Slot {i}: {weap.upper()}",
                value=f"DMG: {stats['dmg']} | Range: {stats['range']} | ROF: {stats['fire_rate']}",
                inline=False
            )
    
    embed.set_footer(text="Use !loadout <weapon> to equip")
    await ctx.send(embed=embed)

# ============== LEADERBOARD COMMANDS ==============

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx, stat: str = "kills"):
    """View global leaderboards"""
    stat_map = {
        "kills": lambda p: p.kills,
        "level": lambda p: p.level,
        "wins": lambda p: p.wins,
        "kd": lambda p: calculate_kd(p.kills, p.deaths),
        "matches": lambda p: p.matches,
        "prestige": lambda p: p.prestige,
    }
    
    if stat not in stat_map:
        await ctx.send(f"❌ Available: {', '.join(stat_map.keys())}")
        return
    
    sorted_players = sorted(users_db.items(), key=lambda x: stat_map[stat](x[1]), reverse=True)[:15]
    
    embed = discord.Embed(
        title=f"🏆 {stat.upper()} Leaderboard",
        color=discord.Color.gold()
    )
    
    medals = ["🥇", "🥈", "🥉"]
    
    for rank, (uid, player) in enumerate(sorted_players, 1):
        medal = medals[rank - 1] if rank <= 3 else f"{rank}."
        value = stat_map[stat](player)
        
        if stat == "kd":
            value = f"{value}"
        else:
            value = f"{value:,}"
        
        embed.add_field(
            name=f"{medal} <@{uid}>",
            value=f"**{value}** | Level {player.level}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# ============== TOURNAMENT COMMANDS ==============

@bot.command(name="tournament", aliases=["tourney"])
async def tournament(ctx, action: str = "info"):
    """Tournament commands"""
    action = action.lower()
    
    if action == "info":
        embed = discord.Embed(
            title="🏆 Current Tournament",
            description="Seasonal ranked competition",
            color=discord.Color.gold()
        )
        embed.add_field(name="Format", value="Single Elimination - TDM", inline=True)
        embed.add_field(name="Prize Pool", value="$50,000 CP", inline=True)
        embed.add_field(name="Status", value="Registration Open", inline=True)
        embed.set_footer(text="Use !tournament join to enter")
        await ctx.send(embed=embed)
    
    elif action == "join":
        player = get_player(ctx.author.id)
        if player.level < 10:
            await ctx.send("⚠️ Requires Level 10+")
            return
        
        await ctx.send(f"✅ {ctx.author.mention} registered for tournament!")
    
    elif action == "bracket":
        embed = discord.Embed(title="📊 Tournament Bracket", color=discord.Color.blue())
        embed.description = "Coming soon - Bracket visualization"
        await ctx.send(embed=embed)

# ============== CLAN COMMANDS ==============

@bot.command(name="clan")
async def clan_cmd(ctx, action: str = "info", *args):
    """Clan management"""
    action = action.lower()
    player = get_player(ctx.author.id)
    
    if action == "info":
        if player.clan_id:
            clan = clans.get(player.clan_id, {})
            embed = discord.Embed(title=f"🎖️ {clan.get('name', 'Clan')}", color=discord.Color.purple())
            embed.add_field(name="Tag", value=clan.get('tag', 'N/A'), inline=True)
            embed.add_field(name="Members", value=len(clan.get('members', [])), inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ You're not in a clan. Use `!clan create <name> <tag>`")
    
    elif action == "create":
        if len(args) < 2:
            await ctx.send("❌ Usage: !clan create <name> <tag>")
            return
        
        clan_name = args[0]
        clan_tag = args[1]
        clan_id = f"clan_{ctx.author.id}_{datetime.now().timestamp()}"
        
        clans[clan_id] = {
            "id": clan_id,
            "name": clan_name,
            "tag": clan_tag,
            "leader": ctx.author.id,
            "members": [ctx.author.id],
            "created": datetime.now(),
        }
        
        player.clan_id = clan_id
        player.clan_tag = f"[{clan_tag}]"
        
        await ctx.send(f"✅ Clan **{clan_name}** created! Tag: **[{clan_tag}]**")

# ============== INFO COMMANDS ==============

@bot.command(name="help", aliases=["commands"])
async def help_cmd(ctx):
    """List all commands"""
    embed = discord.Embed(
        title="🎮 Modern Warfare Bot - Command List",
        color=discord.Color.from_rgb(255, 65, 0)
    )
    
    categories = {
        "👤 Profile": [
            "`!profile [user]` - View stats",
            "`!stats` - Alias for profile",
        ],
        "💰 Economy": [
            "`!daily` - Claim daily rewards",
            "`!shop [operators/weapons]` - Browse store",
            "`!buy <item>` - Purchase cosmetics",
            "`!balance` - Check balance",
        ],
        "🎮 Combat": [
            "`!match [gamemode]` - Start ranked match",
            "`!loadout [weapon]` - Manage loadout",
            "`!stats` - View combat stats",
        ],
        "🏆 Competitive": [
            "`!leaderboard [stat]` - View rankings",
            "`!tournament [info/join/bracket]` - Tournament system",
            "`!clan [info/create]` - Clan management",
        ],
    }
    
    for category, commands_list in categories.items():
        embed.add_field(name=category, value="\n".join(commands_list), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="init")
async def initialize(ctx):
    """Initialize your account"""
    player = get_player(ctx.author.id)
    player.cod_points = 500
    player.balance = 5000
    player.username = ctx.author.name
    
    embed = discord.Embed(
        title="✅ Account Initialized",
        description="Welcome to Modern Warfare",
        color=discord.Color.green()
    )
    embed.add_field(name="Starting COD Points", value="500 CP", inline=True)
    embed.add_field(name="Starting Cash", value="$5,000", inline=True)
    embed.add_field(name="Starter Weapons", value="MP5, AK74, M13", inline=True)
    
    await ctx.send(embed=embed)

# ============== ERROR HANDLING ==============

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help`")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission")
    else:
        await ctx.send(f"❌ Error: {str(error)[:100]}")

# ============== RUN ==============

if __name__ == "__main__":
    bot.run(TOKEN)
