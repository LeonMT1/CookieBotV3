import asyncio
import datetime
import random

import aiosqlite
import discord
from discord import Option
from discord.commands import slash_command
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
from data.textdata import stories
from data.textdata import password
from data.textdata import email


class LVLSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = "database.db"
        self.guild = 724602228505313311
        self.role = 1055216204878446754
        self.halfxpchannel = [1073159625681162260, 1137733329731461242, 1163557292092956765, 1138040937331834881,
                              963741261699874837]
        self.xp = random.randint(15, 25)

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
        async with aiosqlite.connect(self.DB) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                msg_count INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                cookies INTEGER DEFAULT 0,
                call_sec INTEGER DEFAULT 0,
                crate INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_daily TEXT DEFAULT NULL,
                flag_skips INTEGER DEFAULT 0,
                flag_streak INTEGER DEFAULT 0)""")
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
        async with aiosqlite.connect(self.DB) as db:
            guild: discord.Guild = self.bot.get_guild(self.guild)
            rolle: discord.Role = guild.get_role(self.role)
            rndm = random.randint(1, 100)

            if message.author.bot or message.guild.id != guild.id:
                return
            xp = self.xp
            if rolle in message.author.roles:
                xp *= 1.5
            if message.channel.id in self.halfxpchannel:
                xp /= 2

            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.author.id,))
            await db.execute("UPDATE users SET msg_count = msg_count + 1, xp = xp + ? WHERE user_id = ?",
                             (xp, message.author.id))
            await db.commit()
            print(f"{message.author} +{xp} for message")

            embed = discord.Embed(title="Belohnung",
                                  description=f"{message.author.name} hat {xp} Cookies bekommen, da er am Chat "
                                              f"teilgenommen hat!",
                                  color=discord.Color.green())

            if rndm == 1:
                await message.channel.send(embed=embed)
                await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?",
                                 (xp, message.author.id))
                await db.commit()

        new_xp = await self.get_xp(message.author.id)
        old_level = self.get_level(new_xp - xp)
        new_level = self.get_level(new_xp)
        lvlcookies = new_level * 5

        if old_level == new_level:
            return

        embed = discord.Embed(title="Rangaufstieg", color=discord.Color.random(),
                              description=f"Herzlichen Glückwunsch {message.author.mention} du hast Level **{new_level}"
                                          f"** erreicht! Du hast **{lvlcookies}** Cookies als Geschenk bekommen!")

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
        async with aiosqlite.connect(self.DB) as db:

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

    @slash_command(description="Gebe einen anderen User Kekse!")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def gift(self, ctx, user: discord.Member, betrag: Option(int, description="Wie viel möchtest du geben?")):
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                print(f"{ctx.author} hat /give gemacht")
                if betrag < 1:
                    msg = "Du musst mindestens 1 Cookie geben."
                elif user == ctx.author:
                    msg = "Du kannst dir nicht selber Kekse geben!"
                elif user.bot:
                    msg = "Das ist zwar nett gemeint aber die Bots verdienen genug."
                elif result[0] < betrag:
                    msg = "Du hast nicht genug Cookies."
                else:
                    msg = None

                if msg:
                    await ctx.respond(msg, ephemeral=True)
                    return
                else:
                    await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (betrag, user.id))
                    await db.execute("UPDATE users SET cookies = cookies - ? WHERE user_id = ?", (betrag,
                                                                                                  ctx.author.id))
                    await db.commit()
                    embed = discord.Embed(title="Kekse verschenkt!", color=discord.Color.green(),
                                          description=f"Du hast **{betrag}** Cookies an {user.name} verschenkt.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (user.id,)) as cursor2:
                        userresult = await cursor2.fetchone()
                    try:
                        await user.send(f"Du hast von {ctx.author.name} **{betrag}** Cookies bekommen. Du hast jetzt "
                                        f"**{userresult[0]}** Cookies.")
                    except discord.Forbidden:
                        print(f"{user.name} konnte keine DM geschickt werden.")

    @slash_command(description="Lasse dir dein Rank und den von anderen anzeigen!")
    async def rank(self, ctx, member: Option(discord.Member, description="Von welchen User möchtest du den Rank wissen"
                                                                         "?", default=None)):
        print(f"{ctx.author.name} hat /rank gemacht.")
        if member is None:
            member = ctx.author
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (member.id,)) as cursor:
                cookies = await cursor.fetchone()

        if member.bot:
            embed = discord.Embed(title=f"Bots können kein Level haben.", color=discord.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
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
        background.text((490, 125), f"Level {lvl} & {cookies[0]} Cookies", color="#00ced1", font=desc,
                        align="center")
        file = discord.File(fp=background.image_bytes, filename="rank.png")
        await ctx.respond(file=file)

    @slash_command()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        async with aiosqlite.connect(self.DB) as db:
            print(f"{ctx.author} hat /daily gemacht")
            async with db.execute("SELECT streak, last_daily FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                streak = result[0] if result else 0
                last_daily = result[1] if result else None

            now = datetime.datetime.utcnow()
            if last_daily:
                last_daily = datetime.datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S")
                if now.date() == last_daily.date():
                    await ctx.respond("Du hast bereits deine tägliche Belohnung heute abgeholt.", ephemeral=True)
                    return
                if (now - last_daily).days == 1:
                    streak += 1
                elif (now - last_daily).days > 1:
                    streak = 1
            else:
                streak = 1

            await db.execute("UPDATE users SET streak = ?, last_daily = ? WHERE user_id = ?",
                             (streak, now.strftime("%Y-%m-%d %H:%M:%S"), ctx.author.id))
            await db.commit()

            cookies = random.randint(5, 15)
            cookies = cookies + streak
            if streak > 0:
                txtstreak = f"Du bekommst **{cookies} Cookies & 1 Kiste**\nStreak: **{streak}** Tage �"
            else:
                txtstreak = f"Du bekommst **{cookies} Cookies & 1 Kiste**"
            embed = discord.Embed(title="Tägliche Belohnung!", color=discord.Color.green(),
                                  description=txtstreak)
            await db.execute("UPDATE users SET crate = crate + 1 WHERE user_id = ?", (ctx.author.id,))
            await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookies, ctx.author.id))
            await db.commit()
            await ctx.respond(embed=embed)
            print(f"{ctx.author} hat durch /daily {cookies} Cookies bekommen und hat eine Streak von {streak} Tagen.")

    @slash_command()
    async def crates_storage(self, ctx):
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute("SELECT crate FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                if result is None or result[0] == 0:
                    await ctx.respond("Du hast keine Kisten.", ephemeral=True)
                    return
                embed = discord.Embed(title="Kisten", description=f"Du hast **{result[0]}** Kisten.",
                                      color=discord.Color.green())
                await ctx.respond(embed=embed, ephemeral=True)

    @slash_command()
    async def crate(self, ctx):
        async with aiosqlite.connect(self.DB) as db:
            print(f"{ctx.author} hat /crate gemacht")
            flag = random.randint(1, 1)
            cookies = random.randint(10, 30)
            embed = discord.Embed(title="Kiste geöffnet!", color=discord.Color.green(),
                                  description=f"Du hast **{cookies}** Cookies erhalten!")
            async with db.execute("SELECT crate FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                if result[0] <= 0:
                    await ctx.respond("Du hast keine Kisten.", ephemeral=True)
                    return
                await db.execute("UPDATE users SET crate = crate - 1 WHERE user_id = ?", (ctx.author.id,))
                await db.commit()
                await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookies, ctx.author.id))
                await db.commit()
                loading_message = await ctx.respond("📦 Du öffnest eine Kiste...")
                progress_bar = "🟥" * 10
                for i in range(11):
                    filled_bar = "🟩" * i
                    await loading_message.edit(
                        content=f"📦 Kiste wird geöffnet...\n[{filled_bar}{progress_bar[i:]}] {i * 10}%")
                    await asyncio.sleep(0.5)
                await asyncio.sleep(1)
                if flag == 1:
                    embed = discord.Embed(title="Kiste geöffnet!", color=discord.Color.green(),
                                          description="Du hast einen Flaggen-Skip erhalten! Du kannst jetzt einmal"
                                                      " eine Flagge überspringen.")
                    await db.execute("UPDATE users SET crate = crate - 1 WHERE user_id = ?", (ctx.author.id,))
                    await db.commit()
                    await db.execute("UPDATE users SET flag_skip = flag_skip + 1 WHERE user_id = ?",
                                     (ctx.author.id,))
                    await db.commit()
                    await loading_message.edit(content=None, embed=embed)
                    print(f"{ctx.author} hat durch /crate einen Flaggen-Skip bekommen.")
                else:
                    await db.execute("UPDATE users SET crate = crate - 1 WHERE user_id = ?", (ctx.author.id,))
                    await db.commit()
                    await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookies,
                                                                                                  ctx.author.id))
                    await db.commit()
                    await loading_message.edit(content=None, embed=embed)
                    print(f"{ctx.author} hat durch /crate {cookies} Cookies bekommen.")

    @slash_command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def hack(self, ctx, member: Option(discord.Member)):
        print(f"{ctx.author} hat /hack gemacht")
        async with aiosqlite.connect(self.DB) as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (member.id,)) as cursor:
                result = await cursor.fetchone()
            failchance = random.randint(1, 16)
            cookies = random.randint(3, 13)
            stages = ["💻 Verbinden mit Server...",
                      "🔓 Firewall umgehen...",
                      "📂 Daten extrahieren...",
                      "🔑 Zugangsdaten entschlüsseln...",
                      f"✉ Email: {member.name}@{random.choice(email)}",
                      f"🔑 Passwort: {random.choice(password)}",
                      "📡 Verbindung stabilisieren...",
                      "⏳ Datenübertragung...",
                      "💾 Lokale Speicherung...",
                      "🧑‍💻 Zugriff gesichert!"]
            embed = discord.Embed(title="💻 Hack abgeschlossen!",
                                  description=f"Erfolgreich **{cookies}** Cookies gestohlen! 🍪",
                                  color=discord.Color.green())
            failembed = discord.Embed(title="💻 Hack fehlgeschlagen!",
                                      description="Der Hack ist leider fehlgeschlagen, hoffentlich erwischt dich "
                                                  "trotzdem keiner.",
                                      color=discord.Color.red())
            if member.bot:
                embed = discord.Embed(title="Der Bot ist zu stark!",
                                      description="Du kannst den Bot leider nicht Hacken da seine Firewall zu stark "
                                                  "ist.",
                                      color=discord.Color.red())
                await ctx.author.send(embed=embed, ephemeral=True)
                return print(f"{ctx.author} hat versucht einen Bot zu hacken")

            elif result[0] is None:
                await ctx.respond(embed=failembed)
                failembed.set_footer(text="Es gab einen Fehler mit der Datenbank.")
                return print(f"!!!{ctx.author} hat versucht {member} zu hacken aber es gab einen Datenbank Fehler!!!")

            elif result[0] < cookies:
                await ctx.respond(embed=failembed)
                failembed.set_footer(text=f"Du konntest {member.name} nicht Hacken da er sehr wenig Cookies hat.")
                return print(f"{ctx.author} hat versucht einen Armen User zu Hacken")

            elif failchance == 1:
                loading_message = await ctx.respond("💻 Hack wird initialisiert...")
                progress_bar = "🟥" * 10
                for i in range(11):
                    current_stage = stages[min(i, len(stages) - 1)]
                    filled_bar = "🟩" * i
                    await loading_message.edit(
                        content=f"{current_stage}\n[{filled_bar}{progress_bar[i:]}] {i * 10}%")
                    await asyncio.sleep(random.uniform(0.1, 0.9))
                await loading_message.edit(content=None, embed=failembed)
                failembed.set_footer(text="Heute ist einfach nicht dein Tag :(")
                return print(f"{ctx.author}s Hack scheiterte")

            else:
                loading_message = await ctx.respond("💻 Hack wird initialisiert...")
                progress_bar = "🟥" * 10
                for i in range(11):
                    current_stage = stages[min(i, len(stages) - 1)]
                    filled_bar = "🟩" * i
                    await loading_message.edit(
                        content=f"{current_stage}\n[{filled_bar}{progress_bar[i:]}] {i * 10}%")
                    await asyncio.sleep(random.uniform(0.1, 1.9))

                await db.execute("UPDATE users SET cookies = cookies - ? WHERE user_id = ?",
                                 (cookies, member.id))
                await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?",
                                 (cookies, ctx.author.id))
                await db.commit()

                await loading_message.edit(content=None, embed=embed)
                print(f"{ctx.author} hat von {member} {cookies} Cookies gehackt")

    @slash_command()
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def event(self, ctx):
        print(f"{ctx.author} hat /events gemacht")
        async with aiosqlite.connect(self.DB) as db:
            cookies_change = random.randint(-5, 5)

            if cookies_change > 0:
                story = random.choice(stories['positive']).format(cookies_change)
            elif cookies_change < 0:
                story = random.choice(stories['negative']).format(abs(cookies_change))
            else:
                story = "Heute hast du weder Cookies gewonnen noch verloren."

            await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookies_change,
                                                                                          ctx.author.id))
            await db.commit()
            embed = discord.Embed(title="Event", description=story, color=discord.Color.green())
            await ctx.respond(embed=embed)
            print(f"{ctx.author} hat durch /events {cookies_change} Cookies bekommen.")


def setup(bot):
    bot.add_cog(LVLSystem(bot))
