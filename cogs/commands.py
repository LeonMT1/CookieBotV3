from discord.ext import commands
from discord import Option
import requests


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="duden", description="Prüfe ein Wort oder bekomme die Definition.",)
    async def duden(self, ctx, wort: Option(str, "Das Wort, das du prüfen möchtest", required=True),
                    option: Option(str, "Option wählen: 'Prüfen' oder 'Definition'", choices=["Prüfen", "Definition"],
                                   required=True)):
        if option == "Prüfen":
            await self.pruefen(ctx, wort)
        elif option == "Definition":
            await self.definition(ctx, wort)

    async def pruefen(self, ctx, wort):
        # Beispiel-URL, die du durch die tatsächliche API-URL ersetzen musst
        url = f"https://api.duden.de/v1/spellcheck/{wort}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data['correct']:
                await ctx.send(f"'{wort}' ist richtig geschrieben.")
            else:
                await ctx.send(f"'{wort}' ist nicht richtig geschrieben. Meintest du '{data['suggestion']}'?")
        else:
            await ctx.send(f"Es gab ein Problem beim Prüfen des Wortes '{wort}'.")

    async def definition(self, ctx, wort):
        # Beispiel-URL, die du durch die tatsächliche API-URL ersetzen musst
        url = f"https://api.duden.de/definition/{wort}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            definition = data.get('definition', 'Keine Definition gefunden.')
            await ctx.send(f"Definition von '{wort}': {definition}")
        else:
            await ctx.send(f"Es gab ein Problem beim Abrufen der Definition für '{wort}'.")


def setup(bot):
    bot.add_cog(Commands(bot))
