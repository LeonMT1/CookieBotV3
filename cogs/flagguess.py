import asyncio

import aiosqlite
import discord
from discord import slash_command
from discord.ext import commands
import random


class FlagGuessingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guessing_channel = 1163557292092956765
        self.flag_dict = {
            "🇦🇫": "Afghanistan",
            "🇦🇱": "Albanien",
            "🇩🇿": "Algerien",
            "🇦🇩": "Andorra",
            "🇦🇴": "Angola",
            "🇦🇬": "Antigua und Barbuda",
            "🇦🇷": "Argentinien",
            "🇦🇲": "Armenien",
            "🇦🇺": "Australien",
            "🇦🇹": "Österreich",
            "🇦🇿": "Aserbaidschan",
            "🇧🇸": "Bahamas",
            "🇧🇭": "Bahrain",
            "🇧🇩": "Bangladesch",
            "🇧🇧": "Barbados",
            "🇧🇾": "Belarus",
            "🇧🇪": "Belgien",
            "🇧🇿": "Belize",
            "🇧🇯": "Benin",
            "🇧🇹": "Bhutan",
            "🇧🇴": "Bolivien",
            "🇧🇦": "Bosnien und Herzegowina",
            "🇧🇼": "Botswana",
            "🇧🇷": "Brasilien",
            "🇧🇳": "Brunei",
            "🇧🇬": "Bulgarien",
            "🇧🇫": "Burkina Faso",
            "🇧🇮": "Burundi",
            "🇨🇻": "Kap Verde",
            "🇰🇭": "Kambodscha",
            "🇨🇲": "Kamerun",
            "🇨🇦": "Kanada",
            "🇨🇫": "Zentralafrikanische Republik",
            "🇹🇩": "Tschad",
            "🇨🇱": "Chile",
            "🇨🇳": "China",
            "🇨🇴": "Kolumbien",
            "🇰🇲": "Komoren",
            "🇨🇩": "Demokratische Republik Kongo",
            "🇨🇬": "Republik Kongo",
            "🇨🇷": "Costa Rica",
            "🇨🇮": "Elfenbeinküste",
            "🇭🇷": "Kroatien",
            "🇨🇺": "Kuba",
            "🇨🇾": "Zypern",
            "🇨🇿": "Tschechien",
            "🇩🇰": "Dänemark",
            "🇩🇯": "Dschibuti",
            "🇩🇲": "Dominica",
            "🇩🇴": "Dominikanische Republik",
            "🇪🇨": "Ecuador",
            "🇪🇬": "Ägypten",
            "🇸🇻": "El Salvador",
            "🇬🇶": "Äquatorialguinea",
            "🇪🇷": "Eritrea",
            "🇪🇪": "Estland",
            "🇸🇿": "Eswatini",
            "🇪🇹": "Äthiopien",
            "🇫🇯": "Fidschi",
            "🇫🇮": "Finnland",
            "🇫🇷": "Frankreich",
            "🇬🇦": "Gabun",
            "🇬🇲": "Gambia",
            "🇬🇪": "Georgien",
            "🇩🇪": "Deutschland",
            "🇬🇭": "Ghana",
            "🇬🇷": "Griechenland",
            "🇬🇩": "Grenada",
            "🇬🇹": "Guatemala",
            "🇬🇳": "Guinea",
            "🇬🇼": "Guinea-Bissau",
            "🇬🇾": "Guyana",
            "🇭🇹": "Haiti",
            "🇭🇳": "Honduras",
            "🇭🇺": "Ungarn",
            "🇮🇸": "Island",
            "🇮🇳": "Indien",
            "🇮🇩": "Indonesien",
            "🇮🇷": "Iran",
            "🇮🇶": "Irak",
            "🇮🇪": "Irland",
            "🇮🇱": "Israel",
            "🇮🇹": "Italien",
            "🇯🇲": "Jamaika",
            "🇯🇵": "Japan",
            "🇯🇴": "Jordanien",
            "🇰🇿": "Kasachstan",
            "🇰🇪": "Kenia",
            "🇰🇮": "Kiribati",
            "🇰🇵": "Nordkorea",
            "🇰🇷": "Südkorea",
            "🇽🇰": "Kosovo",
            "🇰🇼": "Kuwait",
            "🇰🇬": "Kirgisistan",
            "🇱🇦": "Laos",
            "🇱🇻": "Lettland",
            "🇱🇧": "Libanon",
            "🇱🇸": "Lesotho",
            "🇱🇷": "Liberia",
            "🇱🇾": "Libyen",
            "🇱🇮": "Liechtenstein",
            "🇱🇹": "Litauen",
            "🇱🇺": "Luxemburg",
            "🇲🇰": "Nordmazedonien",
            "🇲🇬": "Madagaskar",
            "🇲🇼": "Malawi",
            "🇲🇾": "Malaysia",
            "🇲🇻": "Malediven",
            "🇲🇱": "Mali",
            "🇲🇹": "Malta",
            "🇲🇭": "Marshallinseln",
            "🇲🇷": "Mauretanien",
            "🇲🇺": "Mauritius",
            "🇲🇽": "Mexiko",
            "🇫🇲": "Mikronesien",
            "🇲🇩": "Moldawien",
            "🇲🇨": "Monaco",
            "🇲🇳": "Mongolei",
            "🇲🇪": "Montenegro",
            "🇲🇦": "Marokko",
            "🇲🇿": "Mosambik",
            "🇲🇲": "Myanmar",
            "🇳🇦": "Namibia",
            "🇳🇷": "Nauru",
            "🇳🇵": "Nepal",
            "🇳🇱": "Niederlande",
            "🇳🇿": "Neuseeland",
            "🇳🇮": "Nicaragua",
            "🇳🇪": "Niger",
            "🇳🇬": "Nigeria",
            "🇳🇴": "Norwegen",
            "🇴🇲": "Oman",
            "🇵🇰": "Pakistan",
            "🇵🇼": "Palau",
            "🇵🇸": "Palästina",
            "🇵🇦": "Panama",
            "🇵🇬": "Papua-Neuguinea",
            "🇵🇾": "Paraguay",
            "🇵🇪": "Peru",
            "🇵🇭": "Philippinen",
            "🇵🇱": "Polen",
            "🇵🇹": "Portugal",
            "🇶🇦": "Katar",
            "🇷🇴": "Rumänien",
            "🇷🇺": "Russland",
            "🇷🇼": "Ruanda",
            "🇰🇳": "St. Kitts und Nevis",
            "🇱🇨": "St. Lucia",
            "🇻🇨": "St. Vincent und die Grenadinen",
            "🇼🇸": "Samoa",
            "🇸🇲": "San Marino",
            "🇸🇹": "Sao Tome und Principe",
            "🇸🇦": "Saudi-Arabien",
            "🇸🇳": "Senegal",
            "🇷🇸": "Serbien",
            "🇸🇨": "Seychellen",
            "🇸🇱": "Sierra Leone",
            "🇸🇬": "Singapur",
            "🇸🇰": "Slowakei",
            "🇸🇮": "Slowenien",
            "🇸🇧": "Salomonen",
            "🇸🇴": "Somalia",
            "🇿🇦": "Südafrika",
            "🇸🇸": "Südsudan",
            "🇪🇸": "Spanien",
            "🇱🇰": "Sri Lanka",
            "🇸🇩": "Sudan",
            "🇸🇷": "Suriname",
            "🇸🇪": "Schweden",
            "🇨🇭": "Schweiz",
            "🇸🇾": "Syrien",
            "🇹🇼": "Taiwan",
            "🇹🇯": "Tadschikistan",
            "🇹🇿": "Tansania",
            "🇹🇭": "Thailand",
            "🇹🇱": "Osttimor",
            "🇹🇬": "Togo",
            "🇹🇴": "Tonga",
            "🇹🇹": "Trinidad und Tobago",
            "🇹🇳": "Tunesien",
            "🇹🇷": "Türkei",
            "🇹🇲": "Turkmenistan",
            "🇹🇻": "Tuvalu",
            "🇺🇬": "Uganda",
            "🇺🇦": "Ukraine",
            "🇦🇪": "Vereinigte Arabische Emirate",
            "🇬🇧": "Vereinigtes Königreich",
            "🇺🇸": "USA",
            "🇺🇾": "Uruguay",
            "🇺🇿": "Usbekistan",
            "🇻🇺": "Vanuatu",
            "🇻🇦": "Vatikanstadt",
            "🇻🇪": "Venezuela",
            "🇻🇳": "Vietnam",
            "🇾🇪": "Jemen",
            "🇿🇲": "Sambia",
            "🇿🇼": "Simbabwe"
        }

        self.current_flag = None
        self.message = None
        self.cooldown = False
        self.count = 0
        self.db = "database.db"

    @commands.Cog.listener()
    async def on_ready(self):
        print("""            flagguess.py     ✅""")
        self.guessing_channel = self.bot.get_channel(self.guessing_channel)
        await self.start_new_game()

    async def start_new_game(self):
        await asyncio.sleep(15)
        self.cooldown = False
        self.current_flag = random.choice(list(self.flag_dict.keys()))
        await self.guessing_channel.send(f"Errate folgende flagge: {self.current_flag}")

    @commands.Cog.listener()
    async def on_message(self, message):
        async with aiosqlite.connect(self.db) as db:
            if self.cooldown is True:
                return
            else:
                cookies = random.randint(1, 5)
                embed = discord.Embed(title="Richtig!",
                                      description=f"**{message.author.name}** hat die Flagge **{self.current_flag}** "
                                                  f"richtig erraten und bekommt dafür **{cookies}** Cookies.",
                                      color=discord.Color.green())
                if message.author == self.bot.user:
                    return
                if message.channel == self.guessing_channel and self.current_flag is not None:
                    if message.content.lower() == self.flag_dict[self.current_flag].lower():
                        await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?",
                                         (cookies, message.author.id))
                        await db.commit()
                        print(f"{message.author} hat eine Flagge erraten.")
                        await message.add_reaction('✅')
                        await message.channel.send(embed=embed)
                        self.cooldown = True
                        await self.start_new_game()
                        await db.close()
                    else:
                        await message.add_reaction('❌')
                        self.count += 1
                        if self.count == 5:
                            await message.channel.send("Du kannst /skip benutzen, um die Flagge zu überspringen.")
                            self.count = 0
                        await db.close()

    @slash_command()
    async def skip(self, ctx):
        async with aiosqlite.connect(self.db) as db:
            print(f"{ctx.author} hat die Flagge übersprungen.")
            async with db.execute("SELECT cookies, flag_skips FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    embed = discord.Embed(title="Fehler", description="Du hast noch keine Cookies!",
                                          color=discord.Color.red())
                    await ctx.respond(embed=embed, ephemeral=True)
                    return print(f"{ctx.author} hat noch keine Cookies um die Flagge zu skippen.")
                cookies, skips = result
                if skips > 0:
                    embed = discord.Embed(title="Flagge übersprungen!",
                                          description=f"Die Flagge war **{self.flag_dict[self.current_flag]}**",
                                          color=discord.Color.green())
                    embed.set_footer(text=f"Du hat für den Skip einen Flag-Skip benutzt du hast noch {skips - 1}.")
                    await db.execute("UPDATE users SET flag_skips = flag_skips - 1 WHERE user_id = ?", (ctx.author.id,))
                    await db.commit()
                    await ctx.respond(embed=embed)
                    await self.start_new_game()
                    print(f"{ctx.author} hat die Flagge übersprungen mit einen Flag Skip.")
                    await db.close()
                elif cookies < 5:
                    embed = discord.Embed(title="Nicht genügend Cookies!",
                                          description="Du brauchst mindestens 5 Cookies", color=discord.Color.red())
                    await ctx.respond(embed=embed, ephemeral=True)
                    await db.close()
                    return print(f"{ctx.author} hat nicht genügend Cookies um die Flagge zu skippen.")
                else:
                    await db.execute("UPDATE users SET cookies = cookies - 5 WHERE user_id = ?", (ctx.author.id,))
                    await db.commit()
                    embed = discord.Embed(title="Flagge übersprungen!",
                                          description=f"Die Flagge war **{self.flag_dict[self.current_flag]}**",
                                          color=discord.Color.green())
                    embed.set_footer(text=f"Du hast jetzt noch {cookies - 5} Cookies.")
                    await ctx.respond(embed=embed)
                    await self.start_new_game()
                    print(f"{ctx.author} hat die Flagge übersprungen.")
                    await db.close()


def setup(bot):
    bot.add_cog(FlagGuessingCog(bot))
