from datetime import datetime

import aiosqlite
import discord
import pytz
from discord import Option
from discord import slash_command
from discord.ext import commands


class EmbedModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(
            discord.ui.InputText(
                label="Embed Titel",
                placeholder="Schreibe hier den Titel des Embeds!"
            ),
            discord.ui.InputText(
                label="Embed Beschreibung",
                placeholder="Schreibe hier die beschreibung des Embeds!",
                style=discord.InputTextStyle.long
            ),
            discord.ui.InputText(
                label="Embed Footer (optional)",
                placeholder="Schreibe hier den Footer (optional)!",
                required=False
            ),
            *args,
            **kwargs)

    async def callback(self, interaction):
        de = pytz.timezone('Europe/Berlin')

        embed = discord.Embed(
            title=self.children[0].value,
            description=self.children[1].value,
            color=discord.Color.orange(),
            timestamp=datetime.now().astimezone(tz=de)
        )

        footer_text = self.children[2].value
        if footer_text:
            embed.set_footer(text=footer_text)

        await interaction.response.send_message(embed=embed)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = "database.db"

    @commands.Cog.listener()
    async def on_ready(self):
        print("moderation.py ✅")

    @slash_command()
    async def embed(self, ctx):
        print(f"{ctx.author} hat /embed ausgeführt")
        modal = EmbedModal(title="Mache ein Embed")
        await ctx.send_modal(modal)

    @slash_command()
    @commands.has_permissions(administrator=True)
    async def activity(self, ctx,
                       typ: Option(str, choices=["game", "stream"]), name: Option(str),
                       status: Option(str, choices=["online", "abwesend", "Bitte nicht Stören", "offline"]),
                       streamer: Option(str, default='https://twitch.tv/leonmt1_', required=False)):
        print(f"{ctx.author} hat /activity ausgeführt")

        if typ == "game":
            typ = discord.Game(name=name)

        if typ == "stream":
            typ = discord.Streaming(
                name=name,
                url=f"https://twitch.tv/{streamer}"
            )

        if status == "online":
            status = discord.Status.online
        if status == "abwesend":
            status = discord.Status.idle
        if status == "Bitte nicht Stören":
            status = discord.Status.dnd
        if status == "offline":
            status = discord.Status.offline

        embed = discord.Embed(
            title="Aktivität erfolgreich geändert",
            description=f"Typ: {typ}\nName: {name}\nStatus: {status}",
            color=discord.Color.green()
        )

        await self.bot.change_presence(activity=typ, status=status)
        await ctx.respond(embed=embed, ephemeral=True)
        print(f"{ctx.author} hat die Aktivität auf folgende Parameter geändert: typ = {typ}, name = {name}, status = "
              f"{status}, streamer = {streamer}")

    @slash_command()
    @commands.has_permissions(administrator=True)
    async def give(self, ctx, member: discord.Member, cookies: int):
        async with aiosqlite.connect(self.db) as db:
            embed = discord.Embed(title="Cookies erfolgreich verändert", color=discord.Color.green(),
                                  description=f"Der Kontostand von {member.mention} wurde um **{cookies}** Cookies "
                                              f"geändert.")
            embed2 = discord.Embed(title="Cookies verändert", color=discord.Color.green(),
                                   description=f"Dein Kontostand wurde um {cookies} geändert durch einen Admin.")
            await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookies, member.id))
            await db.commit()
            await ctx.respond(embed=embed, ephemeral=True)
            await member.send(embed=embed2)

    @slash_command()
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        await channel.send(message)
        await ctx.respond("Nachricht erfolgreich gesendet!", ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
