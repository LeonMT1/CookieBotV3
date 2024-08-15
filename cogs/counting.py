import asyncio

import aiosqlite
import discord
import discord.commands
from discord.ext import commands


class CountingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.count = 0
        self.previous_author = None
        self.channel = 1073159625681162260

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect("database.db") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS counting (
                                count INTEGER PRIMARY KEY)""")
            await asyncio.sleep(0.3)
            print("""            counting.py      ✅""")
            async with db.execute("SELECT count FROM counting") as cursor:
                count = await cursor.fetchone()
                if count is None:
                    self.count = 0
                    await db.execute("INSERT INTO counting (count) VALUES (0)")
                else:
                    self.count = count[0]
            if self.count == 0:
                await self.bot.get_channel(self.channel).send("**0**")

    @commands.Cog.listener()
    async def on_message(self, message):
        async with aiosqlite.connect("database.db") as db:
            if message.author.bot:
                return
            if 'ㅤ' in message.content.lower():
                await message.delete()
            else:
                embed = discord.Embed(title="Verkackt!", description=f"{message.author.name} hat die Falsche Zahl "
                                                                     f"geschrieben.", color=discord.Color.red())
                embed2 = discord.Embed(title="Verkackt!", description=f"{message.author.name} du kannst nicht alleine "
                                                                      f"Zählen du Egoist.")
                if message.channel.id == self.channel:
                    if message.content.replace(' ', '').isdigit():
                        if self.previous_author == message.author:
                            self.count = 0
                            await db.execute("UPDATE counting SET count = 0")
                            await db.commit()
                            await message.channel.send(embed=embed2)
                            await message.channel.send("**0**")
                        elif int(message.content) == self.count + 1:
                            self.count += 1
                            await db.execute("UPDATE counting SET count = count + 1")
                            await db.commit()
                            self.previous_author = message.author
                            await message.add_reaction('✅')
                            await db.commit()
                        else:
                            self.count = 0
                            await db.execute("UPDATE counting SET count = 0")
                            await db.commit()
                            self.previous_author = None
                            await message.channel.send(embed=embed)
                            await message.channel.send("**0**")
                    elif all(char.isdigit() or char in '+-*/() ' for char in message.content):
                        try:
                            result = eval(message.content)
                            if result == self.count + 1:
                                self.count += 1
                                await db.execute("UPDATE counting SET count = count + 1")
                                await db.commit()
                                self.previous_author = message.author
                                await message.add_reaction('✅')
                                await db.commit()
                            else:
                                self.count = 0
                                await db.execute("UPDATE counting SET count = 0")
                                await db.commit()
                                self.previous_author = None
                                await message.channel.send(embed=embed)
                                await message.channel.send("**0**")
                        except Exception:
                            self.count = 0
                            await db.execute("UPDATE counting SET count = 0")
                            await db.commit()
                            self.previous_author = None
                            await message.channel.send(embed=embed)
                            await message.channel.send("**0**")


def setup(bot):
    bot.add_cog(CountingCog(bot))
