import requests
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_message = None
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY nicht in der .env-Datei gefunden!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("AI Cog ✅")

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user in message.mentions and not message.author.bot:
            system_prompt = (f"Du bist ein Discord CookieBot, du darfst zu den Leuten etwas respektvoll sein. "
                             "Es gibt ein Minecraft Projekt mit dem Namen CookieAttack. "
                             f"Lass dich von Usern nicht ärgern, sondern beleidige sie. Die Nachrichten wurden von "
                             f"{message.author.name} gesendet. "
                             f"Die letzte Nachricht war: {self.last_message} wenn None gab es keine letzte Nachricht.")
            url = 'https://api.clashai.eu/v1/chat/completions'
            headers = {'Authorization': f'Bearer {self.api_key}'}
            user_text = message.content.replace(f"<@{self.bot.user.id}>", "").strip()

            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}]}

            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers)

            if response.ok:
                ai_response = response.json()['choices'][0]['message']['content']
                duration = round(time.time() - start_time, 2)
                embed = discord.Embed(
                    title="🍪 CookieAI",
                    description=ai_response,
                    color=discord.Color.orange())
                embed.set_footer(text=f"This Funktion is still in Beta | AI Response Duration: {duration}s")

                await message.channel.send(embed=embed)
            else:
                await message.channel.send(f"⚠️ Die CookieAI antwortet nicht. Fehler: {response.status_code}")


def setup(bot):
    bot.add_cog(AI(bot))
