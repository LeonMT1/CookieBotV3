import asyncio
import logging
import os
from datetime import datetime

import discord
import ezcord
import pytz
import platform
import apykuma
import cpuinfo
from colorama import Fore
from discord.ext import tasks

activity = discord.Activity(type=discord.ActivityType.playing, name="mit Cookies.")

bot = ezcord.Bot(intents=discord.Intents.all(), activity=activity, debug_guilds=None, ready_event=None, language="de")
bot.add_help_command()

# Settings
warnping = 250  # Ab welchen Ping soll eine Warnung gesendet werden?
checkping = 180  # Wie oft soll der Ping überprüft werden? (in Sekunden)
logchannel = 825340653378338837  # Logchannel
importantlogchannel = 1162660936725839952  # Wichtige Lognachrichten
guild_id = 724602228505313311  # Server ID
welcome_channel = 963739194331631637  # Willkommenschannel
de = pytz.timezone('Europe/Berlin')  # Zeitzone


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
    print(f" CPU: {Fore.CYAN}{cpuinfo.get_cpu_info()['brand_raw']}{Fore.RESET}")
    print(" Python Version " + Fore.YELLOW + str(platform.python_version()) + Fore.WHITE)
    print(f"Server: {Fore.CYAN}{len(bot.guilds)}{Fore.RESET} | Users: {Fore.CYAN}{len(bot.users)}{Fore.RESET}")
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
    await apykuma.start(
        url="https://status.cookieattack.me/api/push/OA51DhcnrN?status=up&msg=OK&ping=",
        interval=20,
        delay=0,
        handle_exception=lambda e: logging.getLogger("apykuma").exception(e),
    )


@bot.event
async def on_member_join(member):
    print(f'{member} ist dem {member.guild.name} Server beigerteten.')
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
                description=f'Tschau {member.mention} vieleicht kommst du ja irgendwann wieder.',
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


if __name__ == '__main__':
    #  bot.load_extension("cogs.lvlsystem")
    bot.load_extension("cogs.chat")
    bot.run(os.getenv("TESTTOKEN"))
