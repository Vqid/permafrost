"""
-----------------------------------

Permafrost Source Code

-----------------------------------

This bot was created by Vqid. <http://vqid.me>

"""

# Libs
import discord
from discord.ext import commands, tasks
import asyncio
import asyncpg
import datetime
import re
from dateutil.relativedelta import relativedelta

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value] * float(key)
            except KeyError:
                raise commands.BadArgument(
                    f"{value} is an invalid time key! h|m|s|d are valid arguments"
                )
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")
        return round(time)

# Cog class
class moderation(commands.Cog):
    # Init function
    def __init__(self, bot):
        self.bot = bot
        self.mute_task = self.check_current_mutes.start()

    def cog_unload(self):
        self.mute_task.cancel()

    @tasks.loop(minutes=5)
    async def check_current_mutes(self):
        currentTime = datetime.datetime.now()
        guildid = await self.bot.db.fetchval(f"SELECT guild_id FROM mutes WHERE mutedAt={currentTime}")
        unmuteTime = await self.bot.db.fetchval(f"SELECT unmuteTime FROM mutes WHERE guild_id={guildid[0]}")
        r = await self.bot.db.fetchrow(f"SELECT id FROM mutes WHERE mutedAt={currentTime} > unmuteTime={unmuteTime[0]}")
        if r is None:
            return
        else:
            guild = self.bot.get_guild(guildid[0])
            member = guild.get_member(int(r[0]))

            role = discord.utils.get(guild.roles, name="Muted")
            if role in member.roles:
                await member.remove_roles(role)
                print(f"Unmuted: {member.display_name}")

            await self.bot.db.execute(f"DELETE FROM mutes WHERE id={r[0]}")

    @check_current_mutes.before_loop
    async def before_check_current_mutes(self):
        await self.bot.wait_until_ready()

    @commands.command(
        name='mute'
    )
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, time: TimeConverter=None):
        redloading = self.bot.get_emoji(755977727500353606)
        checkmark = self.bot.get_emoji(755977332417626152)
        yellowloading = self.bot.get_emoji(755977331855589386)
        greenloading = self.bot.get_emoji(755977660487827536)

        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            muted = discord.Embed(title=f"{redloading} No muted role was found! Please create one called 'Muted'", color=discord.Color.red(), timestamp=ctx.message.created_at)
            muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=muted)
            return
        if (member.id == ctx.message.author.id):
            muted = discord.Embed(title=f"{redloading} Error! You cannot mute yourself.", color=discord.Color.red(), timestamp=ctx.message.created_at)
            muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=muted)
            return
        r = await self.bot.db.fetchval(f"SELECT id FROM mutes WHERE guild_id={ctx.guild.id}")
        print(r)
        if r is not None:
            muted = discord.Embed(title=f"{redloading} Error! This user is already muted!", color=discord.Color.red(), timestamp=ctx.message.created_at)
            muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=muted)

        if time is None:
            try:
                await self.bot.db.execute('''
                    INSERT INTO mutes (id,mutedAt,mutedBy,guild_id) VALUES ($1,$2,$3,$4)
                ''', member.id, datetime.datetime.now(), ctx.author.id, ctx.guild.id)
                await member.add_roles(role)
            except TypeError:
                muted = discord.Embed(title=f"{redloading} Error! That is not a valid timestamp!", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return
        else:
            try:
                unmuteTime = datetime.datetime.now() + relativedelta(seconds=time or None)
                await self.bot.db.execute('''
                    INSERT INTO mutes (id,mutedAt,muteDuration,unmuteTime,mutedBy,guild_id) VALUES ($1,$2,$3,$4,$5,$6)
                ''', member.id, datetime.datetime.now(), time or None, unmuteTime, ctx.author.id, ctx.guild.id)

                await member.add_roles(role)
            except TypeError:
                muted = discord.Embed(title=f"{redloading} Error! That is not a valid timestamp!", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return

        if not time:
            muted = discord.Embed(title=f"{checkmark} Successfully muted {member.display_name} indefinitely.", color=discord.Color.green(), timestamp=ctx.message.created_at)
            muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=muted)
            dm = discord.Embed(title=f"{yellowloading} Alert! You have been punished in {ctx.guild.name}!", timestamp=ctx.message.created_at)
            dm.add_field(name="Punishment", value="Mute", inline=True)
            dm.add_field(name="Duration", value="Indefinite", inline=True)
            dm.set_footer(text=f"You were muted by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await member.send(embed=dm)
        else:
            minutes, seconds = divmod(time, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
            if int(days):
                muted = discord.Embed(title=f"{checkmark} Successfully muted {member.display_name} for {days} day(s).", color=discord.Color.green(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                dm = discord.Embed(title=f"{yellowloading} Alert! You have been punished in {ctx.guild.name}!", timestamp=ctx.message.created_at)
                dm.add_field(name="Punishment", value="Mute", inline=True)
                dm.add_field(name="Duration", value=f"{days} day(s)", inline=True)
                dm.set_footer(text=f"You were muted by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await member.send(embed=dm)
            if int(hours):
                muted = discord.Embed(title=f"{checkmark} Successfully muted {member.display_name} for {hours} hour(s).", color=discord.Color.green(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                dm = discord.Embed(title=f"{yellowloading} Alert! You have been punished in {ctx.guild.name}!", timestamp=ctx.message.created_at)
                dm.add_field(name="Punishment", value="Mute", inline=True)
                dm.add_field(name="Duration", value=f"{hours} hour(s)", inline=True)
                dm.set_footer(text=f"You were muted by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await member.send(embed=dm)
            elif int(minutes):
                muted = discord.Embed(title=f"{checkmark} Successfully muted {member.display_name} for {minutes} minute(s).", color=discord.Color.green(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                dm = discord.Embed(title=f"{yellowloading} Alert! You have been punished in {ctx.guild.name}!", timestamp=ctx.message.created_at)
                dm.add_field(name="Punishment", value="Mute", inline=True)
                dm.add_field(name="Duration", value=f"{minutes} minute(s)", inline=True)
                dm.set_footer(text=f"You were muted by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await member.send(embed=dm)
            elif int(seconds):
                muted = discord.Embed(title=f"{checkmark} Successfully muted {member.display_name} for {seconds} second(s).", color=discord.Color.green(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                dm = discord.Embed(title=f"{yellowloading} Alert! You have been punished in {ctx.guild.name}!", timestamp=ctx.message.created_at)
                dm.add_field(name="Punishment", value="Mute", inline=True)
                dm.add_field(name="Duration", value=f"{seconds} second(s)", inline=True)
                dm.set_footer(text=f"You were muted by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await member.send(embed=dm)

        if time and time < 300:
            await asyncio.sleep(time)

            if role in member.roles:
                await member.remove_roles(role)

            await self.bot.db.execute(f"DELETE FROM mutes WHERE guild_id={ctx.guild.id}")


    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            redloading = self.bot.get_emoji(755977727500353606)
            embed = discord.Embed(title=f"{redloading} Error!", description="Incorrect arguments. Please use .mute <user> <h|m|s|d>", color=discord.Color.red(), timestamp=ctx.message.created_at)
            embed.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=embed, delete_after=20)

    @commands.command(
        name='unmute',
    )
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, arg=None):
        redloading = self.bot.get_emoji(755977727500353606)
        checkmark = self.bot.get_emoji(755977332417626152)
        yellowloading = self.bot.get_emoji(755977331855589386)
        greenloading = self.bot.get_emoji(755977660487827536)
        if arg != None:
            role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not role:
                muted = discord.Embed(title=f"{redloading} No muted role was found! Please create one called 'Muted'", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return
            if (member.id == ctx.message.author.id):
                muted = discord.Embed(title=f"{redloading} Error! You cannot unmute yourself.", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return

            await self.bot.db.execute(f'DELETE FROM mutes WHERE guild_id={ctx.guild.id}')
            if role not in member.roles:
                muted = discord.Embed(title=f"{redloading} Error! This user is not muted!", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return

            result2 = await self.bot.db.execute(f'SELECT mutedBy FROM mutes WHERE guild_id={ctx.guild.id}')
            if result2.isdigit():
                await self.bot.db.execute('''
                INSERT INTO unmutes (guild_id,idunmuted,unmutedBy,mutedBy,reason) VALUES ($1,$2,$3,$4,$5)''', ctx.guild.id, member.id, ctx.message.author.id, int(result2[0]), arg)
            await member.remove_roles(role)
            muted = discord.Embed(title=f"{checkmark} Successfully unmuted {member.display_name} for {arg}!", color=discord.Color.green(), timestamp=ctx.message.created_at)
            muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=muted)
            dm = discord.Embed(title=f"{yellowloading} Alert! Your punishment was revoked in {ctx.guild.name}!", timestamp=ctx.message.created_at)
            dm.add_field(name="Punishment Revoked", value="Mute", inline=True)
            dm.add_field(name="Reason", value=arg, inline=True)
            dm.set_footer(text=f"Your mute was revoked by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await member.send(embed=dm)

        else:
            role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not role:
                muted = discord.Embed(title=f"{redloading} No muted role was found! Please create one called 'Muted'", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return
            if (member.id == ctx.message.author.id):
                muted = discord.Embed(title=f"{redloading} Error! You cannot unmute yourself.", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return

            await self.bot.db.execute(f'DELETE FROM mutes WHERE guild_id={ctx.guild.id}')

            if role not in member.roles:
                muted = discord.Embed(title=f"{redloading} Error! This user is not muted!", color=discord.Color.red(), timestamp=ctx.message.created_at)
                muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
                await ctx.send(embed=muted)
                return

            result2 = await self.bot.db.execute(f'SELECT mutedBy FROM mutes WHERE guild_id={ctx.guild.id}')
            if result2.isdigit():
                await self.bot.db.execute('''
                INSERT INTO unmutes (guild_id,idunmuted,unmutedBy,mutedBy,reason) VALUES ($1,$2,$3,$4,$5)''', ctx.guild.id, member.id, ctx.message.author.id, int(result2[0]), "None")
            await member.remove_roles(role)
            muted = discord.Embed(title=f"{checkmark} Successfully unmuted {member.display_name}!", color=discord.Color.green(), timestamp=ctx.message.created_at)
            muted.set_footer(text=f"Executed by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await ctx.send(embed=muted)
            dm = discord.Embed(title=f"{yellowloading} Alert! Your punishment was revoked in {ctx.guild.name}!", timestamp=ctx.message.created_at)
            dm.add_field(name="Punishment Revoked", value="Mute", inline=True)
            dm.add_field(name="Reason", value="None", inline=True)
            dm.set_footer(text=f"Your mute was revoked by {ctx.message.author}", icon_url=str(ctx.message.author.avatar_url))
            await member.send(embed=dm)


# Setup function
def setup(bot):
    bot.add_cog(moderation(bot))
