import os
import sys
import platform
from datetime import datetime
import logging
import asyncio
import re

import cpuinfo
import discord
import ezcord
import psutil
import pytz
import yaml
from colorama import Fore
from discord.ext import tasks
from dotenv import load_dotenv

if not os.path.exists('logs'):
    os.makedirs('logs')

log_filename = datetime.now().strftime('logs/log_%Y-%m-%d_%H-%M-%S.log')
ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')


class DualStream:
    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2

    def write(self, message):
        self.stream1.write(message)
        self.stream2.write(ansi_escape.sub('', message))

    def flush(self):
        self.stream1.flush()
        self.stream2.flush()


log_file = open(log_filename, 'a', encoding='utf-8')

sys.stdout = DualStream(sys.stdout, log_file)
sys.stderr = DualStream(sys.stderr, log_file)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler(sys.stdout)])

activity = discord.Activity(type=discord.ActivityType.playing, name="mit Cookies.")

bot = ezcord.Bot(intents=discord.Intents.all(), activity=activity, debug_guilds=None, ready_event=None, language="de")
bot.add_help_command()

# Settings
warnping = 250  # Ab welchen Ping soll eine Warnung gesendet werden?
checkping = 180  # Wie oft soll der Ping überprüft werden? (in Sekunden)
logchannel = 825340653378338837  # Log channel
importantlogchannel = 1162660936725839952  # Wichtige Lognachrichten
guild_id = 724602228505313311
welcome_channel = 963739194331631637
de = pytz.timezone('Europe/Berlin')


@tasks.loop(seconds=checkping)
async def check_ping():
    current_ping = bot.latency * 1000
    print(f'Aktueller Ping: {current_ping:.2f} ms')
    if current_ping > warnping:
        channel = bot.get_channel(importantlogchannel)
        await channel.send(f"**Warnung:** Der Bot-Ping ist aktuell über {warnping} ms! Aktueller Ping: "
                           f"{current_ping:.2f} ms")


@bot.event
async def on_ready():
    print(f"{bot.user} ist nun online")
    print(f" OS: {Fore.CYAN}{platform.platform()} / {platform.release()}{Fore.RESET}")
    print(f" CPU: {Fore.CYAN}{cpuinfo.get_cpu_info()['brand_raw']}")
    print(f"  |  Cores: {Fore.CYAN}{psutil.cpu_count(logical=False)} and Threads: {Fore.CYAN}{psutil.cpu_count()}")
    print(f"  |  Usage: {Fore.CYAN}{psutil.cpu_percent(interval=1)}%")
    print(f"  |  Frequency: {round(psutil.cpu_freq().current)} MHz{Fore.RESET}")
    print(f" RAM: {Fore.CYAN}{round(psutil.virtual_memory().total / 1024 ** 3)} GB")
    print(f"  |  Usage: {Fore.CYAN}{round(psutil.virtual_memory().percent)}{Fore.RESET}%")
    print(f" Disk: {Fore.CYAN}{round(psutil.disk_usage('/').total / 1024 ** 3)} GB")
    print(f"  |  Usage: {Fore.CYAN}{round(psutil.disk_usage('/').percent)}%{Fore.RESET}")
    print(" Python Version " + Fore.YELLOW + str(platform.python_version()) + Fore.WHITE)
    print(f"Server: {Fore.CYAN}{len(bot.guilds)}{Fore.RESET} | Users: {Fore.CYAN}{len(bot.users)}{Fore.RESET}")
    print("""
            ━━━Datein━━━━━━Status━━━
            main.py          ✅""")
    online = discord.Embed(
        title='Online',
        description=f'{bot.user} ist online!\nOS: {platform.platform()} / {platform.release()}\n'
                    f'CPU: {cpuinfo.get_cpu_info()["brand_raw"]}\nPython Version: {platform.python_version()}\n'
                    f'Server: {len(bot.guilds)} | Users: {len(bot.users)}',
        color=discord.Color.green(),
        timestamp=datetime.now().astimezone(tz=de))
    await asyncio.sleep(2)
    check_ping.start()
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("mit Cookies"))
    await bot.get_channel(logchannel).send(embed=online)


@bot.event
async def on_member_join(member):
    print(f'{member} ist dem {member.guild.name} Server beigetreten.')
    if member.guild.id == guild_id:
        if member.bot:
            embed = discord.Embed(
                title=f"Der {member.name} Bot ist gejoint.",
                color=discord.Color.green(),
                timestamp=datetime.now().astimezone(tz=de),
            )
            await bot.get_channel(importantlogchannel).send(embed=embed)
            return
        em = discord.Embed(
            title=':wave: Hallo! Cool das du hier her gefunden hast!',
            description=f'Hallo {member.mention} wir hoffen du hast viel Spaß auf diesen Server ;).',
            color=discord.Color.orange(),
            timestamp=datetime.now().astimezone(tz=de),
        )
        em.set_thumbnail(url=member.display_avatar.url)
        em.set_image(
            url="https://media.discordapp.net/attachments/825340653378338837/963556131551191070/ezgif-1-9da174320c.gif")
        await bot.get_channel(welcome_channel).send(embed=em)
    else:
        return


@bot.event
async def on_member_remove(member):
    print(f'{member} hat den {member.guild.name} Server verlassen.')
    if member.guild.id == guild_id:
        if member.bot:
            embed = discord.Embed(
                title=f"Der {member.name} Bot ist geleavt.",
                color=discord.Color.red(),
                timestamp=datetime.now().astimezone(tz=de),
            )
            await bot.get_channel(importantlogchannel).send(embed=embed)
            return
        else:
            em = discord.Embed(
                title=':wave: Tschau! Er war noch viel zu Jung um zu sterben',
                description=f'Tschau {member.mention} vielleicht kommst du ja irgendwann wieder.',
                color=discord.Color.red(),
                timestamp=datetime.now().astimezone(tz=de),
            )
            em.set_thumbnail(url=member.display_avatar.url)
            em.set_image(
                url="https://media.discordapp.net/attachments/825340653378338837/963556131769298954/ezgif-2"
                    "-d70a849863.gif")
            await bot.get_channel(welcome_channel).send(embed=em)
    else:
        return


with open("language.yaml", encoding="utf-8") as file:
    localization = yaml.safe_load(file)

if __name__ == '__main__':
    load_dotenv()
    bot.load_extension("cogs.chat")
    bot.load_extension("cogs.birthday")
    bot.load_extension("cogs.commands")
    bot.load_extension("cogs.counting")
    bot.load_extension("cogs.lvlsystem")
    bot.load_extension("cogs.tictactoe")
    bot.load_extension("cogs.moderation")
    bot.load_extension("cogs.warnsystem")
    bot.load_extension("cogs.flagguess")
    bot.load_extension("cogs.gamba")
    bot.localize_commands(localization)
    bot.run(os.getenv("TESTTOKEN"))
