from discord.ext import commands
from dotenv import load_dotenv
import datetime
import openai
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class KI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("""            ki.py            ✅""")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.lower().startswith("ki") or self.bot.user.mention in message.content:

            msg = await message.channel.send("KI lädt antwort...")

            prompt = f"Mein Name ist {message.author} ich spreche Deutsch und ich sage: {message.content[3:]}"

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Du bist ein ChatBot der nicht nur Freundlich ist dein Name ist "
                                                  f"{self.bot.user} es ist {datetime.datetime.now().astimezone()}."},
                    {"role": "user", "content": prompt}
                ]
            )

            output = response.choices[0].message['content']

            await msg.edit(content=output)
        else:
            return


def setup(bot):
    bot.add_cog(KI(bot))
