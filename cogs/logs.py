"""
-----------------------------------

Permafrost Source Code

-----------------------------------

This bot was created by Vqid. <http://vqid.me>

"""

import discord
from discord.ext import commands
import asyncpg

class logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # Commands
    @commands.group(invoke_without_command=True)
    async def logs(self, ctx):
        embed = discord.Embed(name="Error!", description="To set the logs channel, please use !logs channel #channel_here", color=discord.Color.red())
        await ctx.send(embed=embed)

    @logs.command()
    async def channel(self, ctx, channel : discord.TextChannel):
        if ctx.message.author.guild_permissions.administrator:

            result = await self.bot.db.fetch(f"SELECT channelid FROM logs WHERE guildid = {ctx.guild.id}")
            if result is None:
                await self.bot.db.execute("INSERT INTO logs(guildid,channelid) VALUES ($1,$2)", ctx.guild.id, channel.id)
                embed = discord.Embed(title=f"Successfully set logs channel.", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                await self.bot.db.execute("UPDATE logs SET channelid = $1 WHERE guildid = $2", ctx.guild.id, channel.id)
                embed1= discord.Embed(title=f"Successfully updated logs channel.", color=discord.Color.green())
                await ctx.send(embed=embed1)

        @logs.channel.error
        async def logs_channel_error(self, ctx, error):
            if isinstance(error, commands.MissingRequiredArgument):
                embed = discord.Embed(title="Please the channel you would like to set logs to!", color=discord.Color.red())
                await ctx.send(embed=embed, delete_after=10)


def setup(bot):
  bot.add_cog(logs(bot))
