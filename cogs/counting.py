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
                                count INTEGER PRIMARY KEY,
                                highscore INTEGER DEFAULT 0)""")
            print("""            counting.py      ✅""")
            async with db.execute("SELECT count FROM counting") as cursor:
                row = await cursor.fetchone()
                if row is None:
                    self.count = 0
                    await db.execute("INSERT INTO counting (count) VALUES (0)")
                    await db.commit()
                else:
                    self.count = row[0]
            if self.count == 0:
                async with db.execute("SELECT highscore FROM counting") as cursor:
                    cursor = await cursor.fetchone()
                    await self.bot.get_channel(self.channel).send(f"**0** | Highscore: {cursor[0]}")

    @commands.Cog.listener()
    async def on_message(self, message):
        async with aiosqlite.connect("database.db") as db:
            if message.channel.id == self.channel:
                if message.author.bot:
                    return
                if any(char in message.content for char in ['²', '³', '(', ')']) or 'ㅤ' in message.content.lower():
                    await message.delete()
                    embed = discord.Embed(title="Unerlaubte Rechenoperation!",
                                          description="Erlaubte Operatoren: +, -, /, *.", color=discord.Color.red())
                    return await message.channel.send(embed=embed, delete_after=5)

                embed = discord.Embed(title="Verkackt!",
                                      description=f"{message.author.name} hat die Falsche Zahl geschrieben.",
                                      color=discord.Color.red())
                embed2 = discord.Embed(title="Verkackt!",
                                       description=f"{message.author.name} du kannst nicht alleine Zählen du Egoist.")

                if message.content.replace(' ', '').isdigit():
                    if self.previous_author == message.author:
                        async with db.execute("SELECT highscore FROM counting") as cursor:
                            cursor = await cursor.fetchone()
                            self.count = 0
                            await db.execute("UPDATE counting SET count = 0")
                            await db.commit()
                            await message.channel.send(embed=embed2)
                            await message.channel.send(f"**0** | Highscore: {cursor[0]}")
                    elif int(message.content) == self.count + 1:
                        self.count += 1
                        await db.execute("UPDATE counting SET count = count + 1")
                        await db.execute("UPDATE counting SET highscore = count WHERE count > highscore")
                        await db.commit()
                        self.previous_author = message.author
                        await message.add_reaction('✅')
                    else:
                        async with db.execute("SELECT highscore FROM counting") as cursor:
                            cursor = await cursor.fetchone()
                            self.count = 0
                            await db.execute("UPDATE counting SET count = 0")
                            await db.commit()
                            self.previous_author = None
                            await message.channel.send(embed=embed)
                            await message.channel.send(f"**0** | Highscore: {cursor[0]}")
                elif all(char.isdigit() or char in '+-*/() ' for char in message.content):
                    try:
                        result = eval(message.content)
                        if result == self.count + 1:
                            self.count += 1
                            await db.execute("UPDATE counting SET count = count + 1")
                            await db.execute("UPDATE counting SET highscore = count WHERE count > highscore")
                            await db.commit()
                            self.previous_author = message.author
                            await message.add_reaction('✅')
                        else:
                            async with db.execute("SELECT highscore FROM counting") as cursor:
                                cursor = await cursor.fetchone()
                                self.count = 0
                                await db.execute("UPDATE counting SET count = 0")
                                await db.commit()
                                self.previous_author = None
                                await message.channel.send(embed=embed)
                                await message.channel.send(f"**0** | Highscore: {cursor[0]}")
                    except Exception:
                        async with db.execute("SELECT highscore FROM counting") as cursor:
                            cursor = await cursor.fetchone()
                            self.count = 0
                            await db.execute("UPDATE counting SET count = 0")
                            await db.commit()
                            self.previous_author = None
                            await message.channel.send(embed=embed)
                            await message.channel.send(f"**0** | Highscore: {cursor[0]}")


def setup(bot):
    bot.add_cog(CountingCog(bot))
