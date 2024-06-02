import discord
from discord.ext import commands
from discord.commands import slash_command


class lvlsystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = "level.db"

    @commands.Cog.listener()
    async def on_ready(self):
        print("""
        ---Datein------Status---
        main.py          ✅
        lvlsystem.py     ✅""")


def setup(bot):
    bot.add_cog(lvlsystem(bot))
