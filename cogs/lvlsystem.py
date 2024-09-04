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
        async with aiosqlite.connect("database.db") as db:
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

    @slash_command(description="Gebe einen anderen User Kekse!")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def gift(self, ctx, user: discord.Member, betrag: Option(int, description="Wie viel möchtest du geben?")):
        async with aiosqlite.connect("database.db") as db:
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
        async with aiosqlite.connect("database.db") as db:
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
        async with aiosqlite.connect("database.db") as db:
            print(f"{ctx.author} hat /daily gemacht")
            cookies = random.randint(5, 15)
            embed = discord.Embed(title="Tägliche Belohnung!", color=discord.Color.green(),
                                  description=f"Du bekommst **{cookies} & 1 Kiste**")
            await db.execute("UPDATE users SET crate = crate + 1 WHERE user_id = ?", (ctx.author.id,))
            await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookies, ctx.author.id))
            await db.commit()
            await ctx.respond(embed=embed)
            print(f"{ctx.author} hat durch /daily {cookies} Cookies bekommen.")


def setup(bot):
    bot.add_cog(LVLSystem(bot))
