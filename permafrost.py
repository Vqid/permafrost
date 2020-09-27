"""
-----------------------------------

Permafrost Source Code

-----------------------------------

This bot was created by Vqid. <http://vqid.me>

"""


import discord # Discord.py lib
from discord.ext import commands # Discord Commands lib
import asyncpg # PostgreSQL lib
from pathlib import Path # Path lib
import os # OS lib

bot = commands.Bot(command_prefix=".", case_insensivite=True, owner_id=363092903867842562) # Defining bot

cwd = Path(__file__).parents[0]
cwd = str(cwd)

bot.version = '0.1-DEVELOPMENT'

async def create_db_pool():
    # Connecting to postgres
    bot.db = await asyncpg.create_pool(DATABASE CONNECTION HERE)

@bot.event
async def on_ready(): # On ready event
    # Creating tables
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS logs(
            guildid BIGINT PRIMARY KEY,
            channelid BIGINT
        )
    """)
    await bot.db.execute('''CREATE TABLE IF NOT EXISTS bans(
        guild_id BIGINT PRIMARY KEY,
        idbanner BIGINT,
        idbanned BIGINT,
        name TEXT,
        reason TEXT
    )''')
    await bot.db.execute('''CREATE TABLE IF NOT EXISTS unbans(
        guild_id BIGINT PRIMARY KEY,
        idunbanner BIGINT,
        idunbanned BIGINT,
        name TEXT,
        reason TEXT
    )''')
    await bot.db.execute('''CREATE TABLE IF NOT EXISTS mutes(
        guild_id BIGINT PRIMARY KEY,
        id BIGINT,
        mutedAt DATE,
        unmuteTime DATE,
        mutedBy BIGINT,
        muteDuration INT
    )''')
    await bot.db.execute('''CREATE TABLE IF NOT EXISTS unmutes(
        guild_id BIGINT PRIMARY KEY,
        idunmuted BIGINT,
        unmutedBy BIGINT,
        mutedBy BIGINT,
        reason TEXT
    )''')
    # Printing if successful
    print("Successfully connected to Discord's datacenters!")

# Errors
@bot.event
async def on_command_error(ctx, error):
    ignored = (commands.CommandNotFound, commands.UserInputError, commands.UniqueViolationError)
    if isinstance(error, ignored):
        return

    # Error handling
    if isinstance(error, commands.CommandOnCooldown):
        m, s = divmod(error.retry_after, 60)
        h, m = divmod(m, 60)
        if int(h) is 0 and int(m) is 0:
            redloading = bot.get_emoji(755977727500353606)
            embed = discord.Embed(title=f'{redloading} You must wait {int(s)} seconds to use this command!', color=discord.Color.red())
            embed.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=embed, delete_after=15)
        elif int(h) is 0 and int(m) is not 0:
            redloading = bot.get_emoji(755977727500353606)
            embed2 = discord.Embed(title=f'{redloading} You must wait {int(m)} minutes and {int(s)} seconds to use this command!', color=discord.Color.red())
            embed2.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=embed2, delete_after=15)
        else:
            redloading = bot.get_emoji(755977727500353606)
            embed3 = discord.Embed(title=f'{redloading} You must wait {int(h)} hours, {int(m)} minutes and {int(s)} seconds to use this command!', color=discord.Color.red())
            embed3.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=embed3, delete_after=15)
    elif isinstance(error, commands.CheckFailure):
        redloading = bot.get_emoji(755977727500353606)
        perm = discord.Embed(title=f"{redloading} Sadly, You do not have permission to execute this command.", color=discord.Color.red())
        perm.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
        await ctx.send(embed=perm, delete_after=10)
        return
    raise error


# Cog stuff
if __name__ == '__main__':
    for file in os.listdir(cwd+"/cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")


bot.loop.run_until_complete(create_db_pool())
bot.run("TOKEN")
