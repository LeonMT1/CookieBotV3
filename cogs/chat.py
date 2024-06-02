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
        print("""
        chat.py          ✅""")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Update the last message time for the channel
        self.last_message_time[message.channel.id] = datetime.datetime.utcnow()

        if '?' in message.content:
            print(f'Frage: {message.content} von {message.author}')
            if random.randint(1, 100) == 1:
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

                if non_bot_members:
                    user = random.choice(non_bot_members)

                avatar_url = user.avatar.url if user.avatar else "images/defaultavatar.png"

                webhook = await message.channel.create_webhook(name="Sudo webhook...",
                                                               reason=f"Frage von {message.author}")
                await webhook.send(username=f"{user.name}", avatar_url=avatar_url,
                                   content=f"{random.choice(random_response)}")
                await webhook.delete()
            else:
                print("frage nicht beantwortet")
                return

    @tasks.loop(seconds=10)  # Überprüfe alle 10 Sekunden
    async def check_inactivity(self):
        now = datetime.datetime.utcnow()
        if self.channel_id in self.last_message_time:
            elapsed_time = (now - self.last_message_time[self.channel_id]).total_seconds()
            if elapsed_time > 21600:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    random_questions = [
                        'Was ist deine Lieblingsfarbe?', 'Wie war dein Tag?', 'Was ist dein Lieblingstier?',
                        'Was ist dein Lieblingsessen?', 'Hast du ein Hobby?', 'Was ist dein Lieblingsfilm?',
                        'Hast du Haustiere?', 'Was ist dein Traumreiseziel?', 'Was machst du beruflich?',
                        'Was ist dein Lieblingsbuch?'
                    ]
                    await channel.send(random.choice(random_questions))
                    self.last_message_time[self.channel_id] = now

    @check_inactivity.before_loop
    async def before_check_inactivity(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Chat(bot))
