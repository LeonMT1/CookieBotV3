import asyncio
import random

import aiosqlite
import discord
from discord import Option
from discord.commands import slash_command
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font


class LVLSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = "database.db"

    @staticmethod
    def get_level(xp):
        lvl = 1
        amount = 100

        while True:
            xp -= amount
            if xp < 0:
                return lvl
            lvl += 1
            amount += 75

    @staticmethod
    async def xp_to_next_level(xp):
        lvl = LVLSystem.get_level(xp)
        return 175 + (75 * lvl)

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect("database.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                msg_count INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                cookies INTEGER DEFAULT 0,
                call_sec INTEGER DEFAULT 0,
                crate INTEGER DEFAULT 0)""")
            print("""            lvlsystem.py     ✅""")

    async def check_user(self, user_id):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def get_xp(self, user_id):
        await self.check_user(user_id)
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute("SELECT xp FROM users WHERE user_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
            return result[0]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        async with aiosqlite.connect("database.db") as db:
            channels = [1073159625681162260, 1137733329731461242, 1163557292092956765, 1138040937331834881,
                        963741261699874837]

            if not message.guild:
                return

            guild: discord.Guild = self.bot.get_guild(724602228505313311)
            rolle: discord.Role = guild.get_role(1055216204878446754)
            xp = random.randint(15, 25)

            if rolle in message.author.roles:
                xp = xp * 1.5

            if message.channel.id in channels:
                xp = xp / 2

            rndm = random.randint(1, 100)

            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.author.id,))
            await db.execute("UPDATE users SET msg_count = msg_count + 1, xp = xp + ? WHERE user_id = ?",
                             (xp, message.author.id))
            await db.commit()

            print(xp)

            glueckembed = discord.Embed(title="Kleine Belohnung;)",
                                        description=f"{message.author.name} hat {xp} Cookies bekommen, da er aktiv am "
                                                    f"Chat teilgenommen hat!",
                                        color=discord.Color.green())

            if rndm == 1:
                await message.channel.send(embed=glueckembed)
                await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (xp, message.author.id))
                await db.commit()

        new_xp = await self.get_xp(message.author.id)
        old_level = self.get_level(new_xp - xp)
        new_level = self.get_level(new_xp)
        lvlcookies = new_level * 5

        embed = discord.Embed(title="Rangaufstieg", color=discord.Color.random(),
                              description=f"Herzlichen Glückwunsch {message.author.mention} du hast Level **{new_level}"
                                          f"** erreicht! Du hast **{lvlcookies}** Cookies als Geschenk bekommen!")

        if old_level == new_level:
            return

        async with aiosqlite.connect("database.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?",
                                     (lvlcookies, message.author.id))
                await db.commit()
            await message.channel.send(embed=embed)

    @slash_command(description="Lasse dir die Leaderboards anzeigen!")
    async def leaderboard(self, ctx, leaderboard: Option(str, choices=["Cookies", "Nachrichten", "XP", "Talk", "Memes"],
                                                         description="Wähle eine Leaderboard aus"),
                          member: Option(str, description="Sage wie viele Member angezeigt werden sollen", default=10)):
        desc = ""
        counter = 1
        async with aiosqlite.connect("database.db") as db:

            if leaderboard == "Cookies":
                async with db.execute(
                        "SELECT user_id, cookies FROM users WHERE cookies > 0 ORDER BY cookies DESC LIMIT ?",
                        (member,)) as cursor:
                    async for user_id, cookies in cursor:
                        desc += f"{counter}. **<@{user_id}>** - **{cookies}** {leaderboard}\n"
                        counter += 1

                embed = discord.Embed(title=f"**{leaderboard} Rangliste**", description=desc,
                                      color=discord.Color.orange())
                await ctx.respond(embed=embed)
                return

            if leaderboard == "Nachrichten":
                async with db.execute(
                        "SELECT user_id, msg_count FROM users WHERE msg_count > 0 ORDER BY msg_count DESC LIMIT ?",
                        (member,)) as cursor:
                    async for user_id, msg_count in cursor:
                        desc += f"{counter}. **<@{user_id}>** - **{msg_count}** {leaderboard}\n"
                        counter += 1

                embed = discord.Embed(title=f"**{leaderboard} Rangliste**", description=desc,
                                      color=discord.Color.blue())
                await ctx.respond(embed=embed)
                return

            if leaderboard == "XP":
                async with db.execute("SELECT user_id, xp FROM users WHERE xp > 0 ORDER BY xp DESC LIMIT ?",
                                      (member,)) as cursor:
                    async for user_id, xp in cursor:
                        lvl = self.get_level(xp)
                        desc += f"{counter}. **<@{user_id}>** - **{xp}** {leaderboard} - Level **{lvl}**\n"
                        counter += 1

                embed = discord.Embed(title=f"**{leaderboard} Rangliste**", description=desc,
                                      color=discord.Color.green())
                await ctx.respond(embed=embed)
                return

            if leaderboard == "Talk":
                async with db.execute(
                        "SELECT user_id, call_sec FROM users WHERE call_sec > 0 ORDER BY call_sec DESC LIMIT ?",
                        (member,)) as cursor:
                    async for user_id, call_sec in cursor:
                        desc += f"{counter}. **<@{user_id}>** - **{call_sec}** Sekunden {leaderboard}\n"
                        counter += 1

                embed = discord.Embed(title=f"**{leaderboard} Rangliste**", description=desc,
                                      color=discord.Color.dark_blue())
                await ctx.respond(embed=embed)
                return

            if leaderboard == "Memes":
                async with db.execute(
                        "SELECT user_id, upvote, downvote, memes FROM meme WHERE upvote > 0 ORDER BY upvote DESC LIMIT "
                        "?", (member,)) as cursor:
                    async for user_id, upvote, downvote, memes in cursor:
                        desc += (f"{counter}. **<@{user_id}>** - **{upvote}** UpVote - **{downvote}** DownVote - "
                                 f"**{memes}** {leaderboard}\n")
                        counter += 1

                embed = discord.Embed(title=f"**{leaderboard} Rangliste**", description=desc,
                                      color=discord.Color.blue())
                await ctx.respond(embed=embed)

    @slash_command(description="Gebe einen anderen User Kekse!")
    async def gift(self, ctx, user: discord.Member, betrag: Option(int, description="Wie viel möchtest du geben?")):
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                print(f"{ctx.author} hat /give gemacht")
                if user == ctx.author:
                    await ctx.respond("Du kannst dir nicht selber Kekse geben!", ephemeral=True)
                    return
                if user == user.bot:
                    await ctx.respond("Das ist zwar nett gemeint aber die Bots verdienen genug.", ephemeral=True)
                    return
                if result[0] < betrag:
                    await ctx.respond(f"Du hast nicht genug Cookies, du hast nur **{result[0]}** Cookies.",
                                      ephemeral=True)
                    return
            await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (betrag, user.id))
            await db.execute("UPDATE users SET cookies = cookies - ? WHERE user_id = ?", (betrag, ctx.author.id))
            await db.commit()
            await ctx.respond(f"Du hast erfolgreich **{user.name}** **{betrag}** Cookies gegeben.", ephemeral=True)
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (user.id,)) as cursor2:
                userresult = await cursor2.fetchone()
            await user.send(f"Du hast von {ctx.author.name} **{betrag}** Cookies bekommen. Du hast jetzt "
                            f"**{userresult[0]}** Cookies.")

    @slash_command(description="Esse einen Keks")
    async def eat(self, ctx, cookies: Option(int, description="Wie viele Kekse möchtest du essen?")):
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
            if result[0] < 1:
                await ctx.respond("Du hast keine Cookies.", ephemeral=True)
                return
            guild: discord.Guild = self.bot.get_guild(724602228505313311)
            rolle: discord.Role = guild.get_role(1055216204878446754)
            xpboost = cookies * 5
            await db.execute("UPDATE users SET cookies = cookies - ? WHERE user_id = ?", (cookies, ctx.author.id))
            await db.commit()
            if cookies == 1:
                embed = discord.Embed(title="Du hast einen Keks gegessen!",
                                      description=f"Du hast **{cookies}** Keks gegessen und einen x1.5 XP Boost für "
                                                  f"**{xpboost}** Minuten bekommen!",
                                      color=discord.Color.green())
                await ctx.respond(embed=embed)
                await ctx.author.add_roles(rolle)
                await asyncio.sleep(xpboost * 60)
                await ctx.author.remove_roles(rolle)
                await ctx.author.send(f"Dein XP Boost ist vorbei.")
                return
            embed = discord.Embed(title="Du hast Kekse gegessen!",
                                  description=f"Du hast **{cookies}** Kekse gegessen und einen x1.5 XP Boost für "
                                              f"**{xpboost}** Minuten bekommen!", color=discord.Color.green())
            await ctx.respond(embed=embed)
            await ctx.author.add_roles(rolle)
            await asyncio.sleep(xpboost * 60)
            await ctx.author.remove_roles(rolle)
            await ctx.author.send(f"Dein XP Boost ist vorbei.")

    @slash_command(description="Lasse dir dein Rank und den von anderen anzeigen!")
    async def rank(self, ctx, member: Option(discord.Member, description="Von welchen User möchtest du den Rank wissen"
                                                                         "?", default=None)):
        print(f"{ctx.author.name} hat /rank gemacht.")
        if member is None:
            member = ctx.author
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (member.id,)) as cursor:
                cookies = await cursor.fetchone()

        if member.bot:
            embed = discord.Embed(title=f"Bots haben keine Level.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        background = Editor("img/levelup.png").resize((800, 250))
        avatar = await load_image_async(member.display_avatar.url)
        circle_avatar = Editor(avatar).resize((200, 200)).circle_image()
        titel = Font.poppins(size=50, variant="bold")
        desc = Font.poppins(size=30, variant="bold")
        xp = await self.get_xp(member.id)
        lvl = self.get_level(xp)

        background.paste(circle_avatar, (25, 25))
        background.text((490, 50), f"{member.name}", color="white", font=titel, align="center")
        background.text((490, 125), f"Level {lvl} & {cookies[0]} Cookies", color="#00ced1", font=desc, align="center")

        file = discord.File(fp=background.image_bytes, filename="rank.png")
        await ctx.respond(file=file)


def setup(bot):
    bot.add_cog(LVLSystem(bot))
