import asyncio
import datetime
import random

from discord.ext import commands, tasks


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_message_time = {}
        self.channel_id = 963740046995890176
        self.check_inactivity.start()

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(0.1)
        print("""            chat.py          ✅""")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        self.last_message_time[message.channel.id] = datetime.datetime.utcnow()

        if '?' in message.content:
            if random.randint(1, 10) == 1:
                print(f"Frage von {message.author} beantwortet ({message.content})")
                random_response = [
                    'Ja', 'Nein', 'Vielleicht', 'Ich hab keine Ahnung', 'Frag später nochmal', 'Frag jemand anderen',
                    'Frag mich nicht', 'Ich weiß es nicht', 'Ich kann dir nicht helfen', 'Juckt',
                    'Ich bin ein Bot und dumm', 'Ich hab nur Kekse im Kopf', "Ja", "Nein", "Sicher", "Bestimmt",
                    "SICHER NICHT", "nein du idiot", "Bitte bitte nicht", "Bitte ja", "Wer weiß", "Ich weiß es nicht",
                    "Frag jemanden anderes", "Lass mich in Ruhe!", "Ich kann mich nicht erinnern", "Du auch", "Bruh",
                    "Hoffnung", "Nimm einfach einen Cookie", "wenn du es willst", "niemals",
                    "Wenn ja, dann fress ich nen Besen", "Bestimmt aber wusstest du, dass dich niemand mag?",
                    "Halts Maul, ich bin beschäftigt", "Ich bin zu faul um zu antworten", "Ich bin zu beschäftigt",
                    "Leck Eier", "Mir fällst nichts ein", "Spiel erstmal Elden Ring", "Spiel erstmal Minecraft",
                    "Spiel erstmal Fortnite", "Fass Grass an",
                    "https://media.discordapp.net/attachments/1124052881218216057/1246887861220016218/"
                    "alles-was-zaehlt.png"
                ]

                guild = message.guild

                non_bot_members = [member for member in guild.members if not member.bot]

                user = None
                if non_bot_members:
                    user = random.choice(non_bot_members)

                if user:
                    avatar_url = user.avatar.url if user.avatar else "images/defaultavatar.png"
                else:
                    avatar_url = "images/defaultavatar.png"

                webhook = await message.channel.create_webhook(name="Sudo webhook...",
                                                               reason=f"Frage von {message.author}")
                await webhook.send(username=f"{user.name}", avatar_url=avatar_url,
                                   content=f"{random.choice(random_response)}")
                await webhook.delete()
            else:
                print(f"Frage von {message.author} nicht beantwortet ({message.content})")
                return

    @tasks.loop(seconds=10)
    async def check_inactivity(self):
        now = datetime.datetime.utcnow()
        if self.channel_id in self.last_message_time:
            elapsed_time = (now - self.last_message_time[self.channel_id]).total_seconds()
            if elapsed_time > 21600:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    random_questions = [
                        'Was ist euere Lieblingsfarbe?', 'Wie war euer Tag?', 'Was ist euer Lieblingstier?',
                        'Was ist euer Lieblingsessen?', 'Habt ihr ein Hobby? Wenn ja welche/s?',
                        'Was euer Lieblingsfilm?', 'Habt ihr Haustiere? Wenn ja welche/s?',
                        'Was ist euer Traumreiseziel?', 'Was ist eure Lieblingsserie?', "Was ist euer Lieblingsanime?",
                        'Was ist euer Lieblingslied?', 'Was ist euer Lieblings game?', 'Was habt ihr heute noch vor?',
                        'Was ist euer Lieblingsgetränk?', 'Wer ist euer Lieblings youtuber?',
                        'Wer ist euer Lieblingsstreamer?', 'Schreibt einen random Fakt',
                        'Was würdet ihr tun, wenn ihr 1Mio € hättet?', 'Was würdet ihr tuhen wenn ihr Diktator wärt?',
                        'Was ist euer Lieblingssnack?', 'Wer ist euer Vorbild?', 'Was ist euer Traumberuf?',
                        'Habt ihr Geschwister?', 'Mögt ihr Schnee?', 'Mögt ihr Regen?', 'Mögt ihr Sonne?',
                        'Was ist eure Lieblings Jahreszeit?', 'Kaffee oder Tee?', 'Cola oder Fanta?',
                        'Pepsi oder Cola?', 'Playstation oder Xbox?', 'PC oder Konsole?', 'Hund oder Katze?',
                        'Hase oder Meerschweinchen?', 'Schlechteste Serie?', 'Schlechtester Film?',
                        'Nutella mit oder ohne Butter?', 'Fortnite oder Minecraft?', 'Elden Ring oder Dark Souls?',
                        'Beste Superkraft?', 'Unsichtbar oder fliegen können?', 'Unsterblich oder unendlich Geld?',
                        'Unendlich Wissen oder unendlich Geld?', 'Unendlich Wissen oder unendlich Leben?',
                        'Unendlich Leben oder unendlich Geld?', 'Unendlich Leben oder unendlich Wissen?',
                        'Unnötigste Superkraft?', 'Am liebsten in der Vergangenheit oder Zukunft leben?',
                        'Eher Tag oder Nacht?', 'Eher Sommer oder Winter?', 'Eher Stadt oder Land?',
                        'Eher Meer oder Berge?', 'Eher Flugzeug oder Auto?', 'Eher Zug oder Bus?',
                        'Schlechtestes Geburtstagsgeschenk?', 'Schlechtestes Game?', 'Schlechtestes Essen?',
                        'Schlechteste Serie?', 'Schlechtester Film?', 'Schlechteste Superkraft?',
                        'Schlechteste Fähigkeit?', 'Schlechteste Eigenschaft?', 'Schlechteste Angewohnheit?',
                        'Schlechteste Gewohnheit?', 'Schlechteste Marke?', 'Schlechteste Firma?',
                        'Schlechtester Laden?', 'Schlechtestes Restaurant?', 'Schlechteste Kette?',
                    ]
                    await channel.send(random.choice(random_questions))
                    self.last_message_time[self.channel_id] = now

    @check_inactivity.before_loop
    async def before_check_inactivity(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Chat(bot))