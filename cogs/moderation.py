from datetime import datetime

import aiosqlite
import discord
import pytz
from discord import Option
from discord import slash_command
from discord.ext import commands
from discord.utils import basic_autocomplete


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
        self.channel = 825340653378338837

    @commands.Cog.listener()
    async def on_ready(self):
        print("            moderation.py      ✅")

    @staticmethod
    async def unban_autocomplete(ctx: discord.AutocompleteContext):
        x = await ctx.interaction.guild.bans().flatten()
        x = [f'{y.user}' for y in x]
        return x

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

    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext) -> None:
        channel = self.get_channel(self.channel)
        embed = discord.Embed(
            title=f'/{ctx.command} in {ctx.channel}',
            timestamp=datetime.now(),
            color=discord.Color.purple()
        )
        embed.add_field(name='User', value=ctx.user.mention)
        embed.add_field(name='Channel', value=ctx.channel.mention)

        command = f'/{ctx.command} '
        if ctx.selected_options:
            command += ' '.join(
                (
                    f'**{option["name"]}**:{option["value"]}'
                    for option
                    in ctx.selected_options
                )
            )
        embed.add_field(name='Command', value=command)
        embed.set_author(name=ctx.user.display_name, icon_url=ctx.user.display_avatar)

        print(f'{ctx.user} benutzte {ctx.command} in {ctx.channel}')
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:
            return

        if message.author.avatar is None:
            url = "https://cookieattack.me/img/nopb.png"
        else:
            url = message.author.avatar.url

        if isinstance(message.channel, discord.DMChannel):
            channel = self.bot.get_channel(self.channel)
            embed = discord.Embed(title="", description=f"**{message.content}**", color=discord.Color.blue())
            embed.timestamp = discord.utils.utcnow()
            embed.set_author(name=f"Neue Nachricht von {message.author}", icon_url=url)
            embed.set_thumbnail(url="")
            embed.set_footer(text=f"UserID: {message.author.id}")

            print(f"Privat Nachricht von {message.author}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author == self.bot.user or message.author.bot:
            return

        if message.author.avatar is None:
            url = "https://cookieattack.me/img/nopb.png"
        else:
            url = message.author.avatar.url
        channel = self.bot.get_channel(self.channel)
        embed = discord.Embed(title="", description=f"Nachricht Inhalt: **{message.content}**",
                              color=discord.Color.red())
        embed.timestamp = discord.utils.utcnow()
        embed.set_author(name=f"Nachricht von {message.author} wurde gelöscht", icon_url=url)
        embed.set_thumbnail(url="")
        embed.set_footer(text=f"UserID: {message.author.id}")

        print(f"Nachricht von {message.author} wurde gelöscht")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author == self.bot.user or before.author.bot:
            return

        if before.author.avatar is None:
            url = "https://cookieattack.me/img/nopb.png"
        else:
            url = before.author.avatar.url

        channel = self.bot.get_channel(self.channel)
        embed = discord.Embed(title="", description=f"**Davor:** {before.content}\n**Danach:** {after.content}",
                              color=discord.Color.blue())
        embed.timestamp = discord.utils.utcnow()
        embed.set_author(name=f"Bearbeite Nachricht von {before.author}", icon_url=url)
        embed.set_thumbnail(url="")
        embed.set_footer(text=f"UserID: {before.author.id}")

        print(f"Nachricht von {before.author} wurde bearbeitet")
        await channel.send(embed=embed)

    @slash_command()
    @discord.default_permissions(ban_members=True)
    async def unban(self, ctx: discord.ApplicationContext,
                    user: Option(str, "Wich user do you want to unban",
                                 autocomplete=basic_autocomplete(unban_autocomplete), required=True)):
        channel = self.bot.get_channel(self.channel)
        embed = discord.Embed(
            title='Entbannt',
            description=f'{user} wurde entbannt',
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Entbannt von {ctx.author.name}", icon_url=ctx.author.avatar.url)
        async for ban in ctx.guild.bans():
            if f'{ban.user}' == f'{user}':
                await ctx.guild.unban(ban.user)
                print(f"{ctx.author.name} hat {ban.user} entbannt")
                await channel.send(embed=embed)
                return await ctx.respond(f"{ban.user} wurde entbannt", ephemeral=True)

            else:
                continue

        return await ctx.respond("User kann nicht gefunden werden.", ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
