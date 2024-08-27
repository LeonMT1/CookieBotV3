import asyncio
import datetime

import aiosqlite
import discord
from discord.commands import Option
from discord.ext import commands


class WarnSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database.db'
        bot.loop.create_task(self.init_db())

    async def init_db(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS warnings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        moderator_id INTEGER,
                        reason TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS punishment_settings (
                        warn_count INTEGER PRIMARY KEY,
                        punishment_type TEXT,
                        duration INTEGER
                    )
                ''')
                await db.commit()
        except Exception as e:
            print(f"Fehler bei der Datenbankinitialisierung: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        print("""            warnsystem.py    ✅""")

    @commands.slash_command(name="warn", description="Warnt einen Benutzer")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        try:
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%d.%m.%Y %H:%M")

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO warnings (user_id, moderator_id, reason, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (user.id, ctx.author.id, reason, current_time))
                await db.commit()

                # Zähle die Warnungen des Benutzers
                cursor = await db.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ?', (user.id,))
                warn_count = (await cursor.fetchone())[0]

                # Überprüfe, ob eine Strafe für diese Anzahl von Warnungen festgelegt ist
                cursor = await db.execute(
                    'SELECT punishment_type, duration FROM punishment_settings WHERE warn_count = ?', (warn_count,))
                punishment = await cursor.fetchone()

            embed = discord.Embed(title="Warnung erteilt", color=discord.Color.yellow())
            embed.add_field(name="Benutzer", value=user.mention, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name="Grund", value=reason, inline=False)
            embed.add_field(name="Warnungen", value=str(warn_count), inline=False)
            embed.set_footer(text=f"Datum: {formatted_time}")

            if punishment:
                punishment_type, duration = punishment
                if punishment_type == "kick":
                    await user.kick(reason=f"Automatische Strafe nach {warn_count} Warnungen")
                    embed.add_field(name="Automatische Strafe", value=f"Benutzer wurde gekickt", inline=False)
                elif punishment_type == "ban":
                    await user.ban(reason=f"Automatische Strafe nach {warn_count} Warnungen", delete_message_days=0)
                    embed.add_field(name="Automatische Strafe", value=f"Benutzer wurde gebannt", inline=False)
                elif punishment_type == "mute":
                    until = discord.utils.utcnow() + datetime.timedelta(minutes=duration)
                    await user.timeout(until, reason=f"Automatische Strafe nach {warn_count} Warnungen")
                    embed.add_field(name="Automatische Strafe",
                                    value=f"Benutzer wurde für {duration} Minuten stummgeschaltet", inline=False)

            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"Fehler beim Warnen des Benutzers: {e}", ephemeral=True)

    @commands.slash_command(name="warnings", description="Zeigt die Warnungen eines Benutzers")
    async def warnings(self, ctx, user: discord.Member):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT id, moderator_id, reason, timestamp
                    FROM warnings
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                ''', (user.id,)) as cursor:
                    warnings = await cursor.fetchall()

            if not warnings:
                await ctx.respond(f"{user.mention} hat keine Warnungen.")
                return

            embed = discord.Embed(title=f"Warnungen für {user.name}", color=discord.Color.orange())
            for warn_id, moderator_id, reason, timestamp in warnings:
                moderator = await self.bot.fetch_user(moderator_id)
                formatted_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").strftime(
                    "%d.%m.%Y %H:%M")
                embed.add_field(
                    name=f"Warnung ID: {warn_id}",
                    value=f"**Moderator:** {moderator.mention}\n**Grund:** {reason}\n**Datum:** {formatted_time}",
                    inline=False
                )

            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"Fehler beim Abrufen der Warnungen: {e}", ephemeral=True)

    @commands.slash_command(name="delwarn", description="Löscht eine Warnung anhand der Warn-ID")
    @commands.has_permissions(administrator=True)
    async def delwarn(self, ctx, warn_id: int):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT user_id FROM warnings WHERE id = ?', (warn_id,))
                result = await cursor.fetchone()

                if result is None:
                    await ctx.respond(f"Keine Warnung mit der ID {warn_id} gefunden.", ephemeral=True)
                    return

                user_id = result[0]

                await db.execute('DELETE FROM warnings WHERE id = ?', (warn_id,))
                await db.commit()

            try:
                user = await self.bot.fetch_user(user_id)
                user_mention = user.mention
            except discord.NotFound:
                user_mention = f"Benutzer-ID: {user_id}"

            embed = discord.Embed(title="Warnung gelöscht", color=discord.Color.green())
            embed.add_field(name="Warn-ID", value=str(warn_id), inline=False)
            embed.add_field(name="Betroffener Benutzer", value=user_mention, inline=False)
            embed.add_field(name="Gelöscht von", value=ctx.author.mention, inline=False)

            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"Fehler beim Löschen der Warnung: {e}", ephemeral=True)

    @commands.slash_command(name="allwarnings", description="Zeigt alle Warnungen aller Benutzer")
    @commands.has_permissions(administrator=True)
    async def allwarnings(self, ctx):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT id, user_id, moderator_id, reason, timestamp
                    FROM warnings
                    ORDER BY timestamp DESC
                ''') as cursor:
                    all_warnings = await cursor.fetchall()

            if not all_warnings:
                await ctx.respond("Es gibt keine Warnungen in der Datenbank.")
                return

            pages = []
            for i in range(0, len(all_warnings), 25):
                embed = discord.Embed(title="Alle Warnungen", color=discord.Color.blue())
                for warn_id, user_id, moderator_id, reason, timestamp in all_warnings[i:i + 25]:
                    user = await self.bot.fetch_user(user_id)
                    moderator = await self.bot.fetch_user(moderator_id)
                    formatted_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").strftime(
                        "%d.%m.%Y %H:%M")
                    embed.add_field(
                        name=f"Warnung ID: {warn_id}",
                        value=f"**Benutzer:** {user.mention}\n**Moderator:** {moderator.mention}\n**Grund:** {reason}"
                              f"\n**Datum:** {formatted_time}",
                        inline=False
                    )
                embed.set_footer(text=f"Seite {i // 25 + 1} von {(len(all_warnings) - 1) // 25 + 1}")
                pages.append(embed)

            current_page = 0

            message = await ctx.respond(embed=pages[current_page])

            if len(pages) > 1:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️",
                                                                          "➡️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                        if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "⬅️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)

                        else:
                            await message.remove_reaction(reaction, user)

                    except asyncio.TimeoutError:
                        break

                await message.clear_reactions()
        except Exception as e:
            await ctx.respond(f"Fehler beim Abrufen aller Warnungen: {e}", ephemeral=True)

    @commands.slash_command(name="set_punishment",
                            description="Legt eine Strafe für eine bestimmte Anzahl von Warnungen fest")
    @commands.has_permissions(administrator=True)
    async def set_punishment(self, ctx, warn_count: int,
                             punishment_type: Option(choices=["kick", "mute", "ban", "none"]), duration: int = 0):
        try:
            if punishment_type not in ["kick", "ban", "mute", "none"]:
                await ctx.respond("Ungültiger Straftyp. Erlaubte Werte sind: kick, ban, mute, none", ephemeral=True)
                return

            async with aiosqlite.connect(self.db_path) as db:
                if punishment_type == "none":
                    await db.execute('DELETE FROM punishment_settings WHERE warn_count = ?', (warn_count,))
                else:
                    await db.execute('''
                        INSERT OR REPLACE INTO punishment_settings (warn_count, punishment_type, duration)
                        VALUES (?, ?, ?)
                    ''', (warn_count, punishment_type, duration))
                await db.commit()

            if punishment_type == "none":
                await ctx.respond(f"Strafe für {warn_count} Warnungen wurde entfernt.")
            else:
                await ctx.respond(f"Strafe für {warn_count} Warnungen festgelegt: {punishment_type}" + (
                    f" für {duration} Minuten" if punishment_type == "mute" else ""))
        except Exception as e:
            await ctx.respond(f"Fehler beim Festlegen der Strafe: {e}", ephemeral=True)

    @commands.slash_command(name="show_punishments", description="Zeigt alle festgelegten Strafen")
    @commands.has_permissions(kick_members=True)
    async def show_punishments(self, ctx):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                        'SELECT warn_count, punishment_type, duration FROM punishment_settings ORDER BY '
                        'warn_count') as cursor:
                    punishments = await cursor.fetchall()

            if not punishments:
                await ctx.respond("Es sind keine Strafen festgelegt.")
                return

            embed = discord.Embed(title="Festgelegte Strafen", color=discord.Color.blue())
            for warn_count, punishment_type, duration in punishments:
                if punishment_type == "mute":
                    value = f"{punishment_type} für {duration} Minuten"
                else:
                    value = punishment_type
                embed.add_field(name=f"{warn_count} Warnungen", value=value, inline=False)

            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"Fehler beim Abrufen der Strafen: {e}", ephemeral=True)

    @commands.slash_command(name="del_punishments", description="Löscht alle festgelegten Strafen")
    @commands.has_permissions(administrator=True)
    async def del_punishments(self, ctx):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM punishment_settings')
                await db.commit()

            embed = discord.Embed(title="Strafen gelöscht", color=discord.Color.green())
            embed.description = "Alle festgelegten Strafen wurden erfolgreich gelöscht."
            embed.set_footer(text=f"Ausgeführt von: {ctx.author.name}")

            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"Fehler beim Löschen der Strafen: {e}", ephemeral=True)


def setup(bot):
    bot.add_cog(WarnSystem(bot))
