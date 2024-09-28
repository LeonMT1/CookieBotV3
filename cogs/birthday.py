import aiosqlite
import discord

from discord import slash_command
from discord.ext import commands, tasks
from discord import Option
from datetime import datetime, date


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.avatar = "https://cookieattack.me/img/notbywebsite/defaultavatar.png"
        self.birthdaychannel = 1117422216519368786

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect("database.db") as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS birthday (
                user_id INTEGER PRIMARY KEY,
                day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER DEFAULT NONE
            )""")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_birthday_date ON birthday (day, month)")
            self.check_day.start()
            print("""            birthday.py      ✅""")

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        async with aiosqlite.connect("database.db") as db:
            await db.execute("DELETE FROM birthday WHERE user_id = ?", (member.id,))
            await db.commit()

    @tasks.loop(seconds=50)
    async def check_day(self):
        now = datetime.now()
        if now.hour == 0 and now.minute == 1:
            day_of_week = now.strftime("%A")
            print(f"Es ist: {day_of_week} der {now.day}.{now.month}.{now.year}")
            channel = self.bot.get_channel(self.birthdaychannel)

            async with aiosqlite.connect("database.db") as db:
                cursor = await db.execute("SELECT user_id FROM birthday WHERE day = ? AND month = ?",
                                          (now.day, now.month))
                birthdays_today = await cursor.fetchall()

            for user_id in birthdays_today:
                user = self.bot.get_user(user_id[0])
                if user:
                    await channel.send(f"Herzlichen Glückwunsch zum Geburtstag, {user.mention}!")
        else:
            return

    @slash_command()
    async def set_birthday(self, ctx, day: Option(int, required=True), month: Option(int, required=True),
                           year: Option(int, default=None, required=False)):
        async with aiosqlite.connect("database.db") as db:
            print(f"{ctx.author} hat /set_birthday ausgeführt")
            avatar = ctx.author.avatar.url if ctx.author.avatar else self.avatar

            fail = discord.Embed(title="Fehler", color=discord.Color.red(),
                                 description="Bitte gib ein gültiges Datum an.")
            fail.set_footer(text="Beispiel: /birthday 1 1 2000")
            fail.set_thumbnail(url=avatar)

            embedsus = discord.Embed(title="Erfolgreich", color=discord.Color.green(),
                                     description=f"Dein Geburtstag wurde erfolgreich auf den "
                                                 f"**{day}.{month}** gesetzt.")
            embedsus.set_thumbnail(url=avatar)

            if day < 1 or day > 31 or month < 1 or month > 12 or (year is not None and (year < 1900 or year > 2022)):
                return await ctx.respond(embed=fail, ephemeral=True)

            await db.execute("INSERT OR REPLACE INTO birthday (user_id, day, month, year) VALUES (?, ?, ?, ?)",
                             (ctx.author.id, day, month, year))
            await db.commit()
            await ctx.respond(embed=embedsus, ephemeral=True)
            print(f"{ctx.author} hat seinen Geburtstag auf den {day}.{month}.{year} gesetzt.")

    @slash_command()
    async def delete_birthday(self, ctx):
        async with aiosqlite.connect("database.db") as db:
            print(f"{ctx.author} hat /delete_birthday ausgeführt")
            avatar = ctx.author.avatar.url if ctx.author.avatar else self.avatar

            fail = discord.Embed(title="Fehler", color=discord.Color.red(),
                                 description="Du hast kein Geburtstag eingetragen. Da gibt es nichts zu löschen.")
            fail.set_thumbnail(url=avatar)

            embedsus = discord.Embed(title="Erfolgreich", color=discord.Color.green(),
                                     description="Dein Geburtstag wurde erfolgreich gelöscht.")
            embedsus.set_thumbnail(url=avatar)

            await db.execute("DELETE FROM birthday WHERE user_id = ?", (ctx.author.id,))
            await db.commit()
            await ctx.respond(embed=embedsus, ephemeral=True)
            print(f"{ctx.author} hat seinen Geburtstag gelöscht.")

    @slash_command()
    async def next_birthdays(self, ctx):
        async with aiosqlite.connect("database.db") as db:
            print(f"{ctx.author} hat /next_birthdays ausgeführt")
            fail = discord.Embed(title="Fehler", color=discord.Color.red(),
                                 description="Es sind keine Geburtstage eingetragen.")
            embed = discord.Embed(title="Nächste Geburtstage", color=discord.Color.green())

            cursor = await db.execute("SELECT user_id, day, month, year FROM birthday")
            birthdays = await cursor.fetchall()
            if not birthdays:
                return await ctx.respond(embed=fail, ephemeral=True)

            today = date.today()
            birthday_list = []
            for user_id, day, month, year in birthdays:
                user = self.bot.get_user(user_id)
                if user:
                    next_birthday = date(today.year, month, day)
                    if today > next_birthday:
                        next_birthday = date(today.year + 1, month, day)
                    days_left = (next_birthday - today).days

                    age = None
                    if year:
                        age = today.year - year
                        if (today.month, today.day) >= (month, day):
                            age += 1

                    birthday_list.append((user, days_left, age))

            birthday_list.sort(key=lambda x: x[1])

            birthday_info = ""
            for i, (user, days_left, age) in enumerate(birthday_list, start=1):
                if age is not None:
                    birthday_info += (f"**{i}**. {user.mention} - **{days_left}** Tage bis zum Geburtstag, "
                                      f"wird **{age}** Jahre alt\n")
                else:
                    birthday_info += f"**{i}**. {user.mention} - **{days_left}** Tage bis zum Geburtstag\n"

            embed.description = birthday_info
            await ctx.respond(embed=embed)
            print(f"{ctx.author} hat die nächsten Geburtstage abgefragt.")

    @slash_command()
    async def see_birthday(self, ctx, user: discord.Member = None):
        print(f"{ctx.author} hat /see_birthday ausgeführt")
        if user is None:
            user = ctx.author
        avatar = user.avatar.url if user.avatar else self.avatar
        async with aiosqlite.connect("database.db") as db:

            fail = discord.Embed(title="Fehler", color=discord.Color.red(),
                                 description="Dieser Nutzer hat keinen Geburtstag eingetragen.")
            fail.set_thumbnail(url=avatar)

            cursor = await db.execute("SELECT day, month, year FROM birthday WHERE user_id = ?", (user.id,))
            birthday = await cursor.fetchone()

            if birthday:
                day, month, year = birthday
                if year:
                    await ctx.respond(f"{user.mention} hat am **{day}.{month}.{year}** Geburtstag.", ephemeral=True)
                    print(f"{ctx.author} hat den Geburtstag von {user} abgefragt.")
                else:
                    await ctx.respond(f"{user.mention} hat am **{day}.{month}** Geburtstag.", ephemeral=True)
                    print(f"{ctx.author} hat den Geburtstag von {user} abgefragt.")
            else:
                await ctx.respond(embed=fail, ephemeral=True)
                print(f"{ctx.author} hat den Geburtstag von {user} abgefragt.")

    @slash_command()
    @commands.has_permissions(administrator=True)
    async def admin_birthday(self, ctx, user: discord.Member, day: int, month: int, year: Option(int, default=None,
                                                                                                 required=False)):
        print(f"{ctx.author} hat /admin_birthday ausgeführt")
        if ctx.author.guild_permissions.administrator:
            async with aiosqlite.connect("database.db") as db:
                await db.execute("INSERT OR REPLACE INTO birthday (user_id, day, month, year) VALUES (?, ?, ?, ?)",
                                 (user.id, day, month, year))
                await db.commit()
                await ctx.respond(f"Der Geburtstag von {user.mention} wurde erfolgreich auf den "
                                  f"**{day}.{month}.{year}** gesetzt.", ephemeral=True)
                print(f"{ctx.author} hat den Geburtstag von {user} auf den {day}.{month}.{year} geändert.")
        else:
            fail = discord.Embed(title="Fehler", color=discord.Color.red(),
                                 description="Es gab einen Fehler. Entweder du hast ein ungültiges Datum angegeben "
                                             "oder du hast keine Rechte um diesen Befehl auszuführen.")
            await ctx.respond(embed=fail, ephemeral=True)
            print(f"{ctx.author} hat versucht den Geburtstag von {user} zu setzen.")

    @slash_command()
    @commands.has_permissions(administrator=True)
    async def admin_delete_birthday(self, ctx, user: discord.Member):
        async with aiosqlite.connect("database.db") as db:
            print(f"{ctx.author} hat /admin_delete_birthday ausgeführt")
            embed = discord.Embed(title="Erfolgreich", color=discord.Color.green(),
                                  description=f"Der Geburtstag von {user.mention} wurde erfolgreich gelöscht.")
            await db.execute("DELETE FROM birthday WHERE user_id = ?", (user.id,))
            await db.commit()
            await ctx.respond(embed=embed, ephemeral=True)
            print(f"{ctx.author} hat den Geburtstag von {user} gelöscht.")


def setup(bot):
    bot.add_cog(Birthday(bot))
