import os
import random

import aiosqlite
import discord
import discord.commands
from discord.ext import commands
from github import Github


class BugReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bugchannel = 1071805141591793806
        self.modchannel = 1071805178312917105

    @commands.Cog.listener()
    async def on_ready(self):
        print("""            bugreport.py     ✅""")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id == self.bugchannel:
            channel = self.bot.get_channel(self.modchannel)
            embed = discord.Embed(title=f"**Neuer Bug wurde von {message.author.name} eingereicht:**",
                                  description=message.content)
            await channel.send(embed=embed, view=BugView(message.author))
            await message.delete()


def setup(bot):
    bot.add_cog(BugReport(bot))


class BugView(discord.ui.View):
    def __init__(self, user):
        self.user = user
        super().__init__(timeout=None)
        self.devrole = 1162854899030171748
        self.modchannel = 1071805178312917105

    @discord.ui.button(label="✅", style=discord.ButtonStyle.green)
    async def button_callback1(self, button, interaction):
        async with aiosqlite.connect("database.db") as db:
            cookie = random.randint(10, 20)
            g = Github(os.getenv('GITHUB_AUTH_TOKEN'))
            repo = g.get_repo("LeonMT1/CookieBotV3")

            embed = discord.Embed(title="Bestätigt", color=discord.Color.green(),
                                  description=f"Du hast durch das Reporten eines Bugs **{cookie}** Cookies erhalten.", )
            await self.user.send(f"Dein Bug wurde bestätigt, du bekommst {cookie} Cookies.", embed=embed)

            await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (cookie, self.user.id))
            await db.commit()

            # repo.create_issue(title=f"Bug von {self.user.name} eingereicht",
            #                  body=f"{interaction.message.embeds[0].description}")

            role_id = self.devrole
            roledev = interaction.guild.get_role(role_id)
            for member in roledev.members:
                await member.send(f"Ein neuer Bug wurde von {self.user.name} eingereicht. Schaue auf GitHub "
                                  f"(https://github.com/LeonMT1/CookieBotV3/) für mehr Informationen.")

            self.disable_all_items()
            await interaction.response.send_message(f"Bug wurde bestätigt, der Member bekommt {cookie} Cookies")
            await interaction.message.edit(view=self)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.red)
    async def button_callback2(self, button, interaction):
        embed = discord.Embed(title="Abgelehnt", color=discord.Color.red(),
                              description="Dein Bug wurde nicht von unseren Mods angenommen.")
        await self.user.send("Dein Bug wurde nicht angenommen.", embed=embed)

        self.disable_all_items()

        await interaction.response.send_message("Bug wurde nicht bestätigt, der Member bekommt keine Cookies.")
        await interaction.message.edit(view=self)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True
