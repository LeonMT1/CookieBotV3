import aiohttp
import aiosqlite
import discord
from discord.ext import commands, tasks
from translate import Translator


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator(to_lang="de")
        self.post_wyr_question.start()
        self.report_results.start()
        self.db_path = 'database.db'
        self.bot.loop.create_task(self.init_db())
        self.first_report_skipped = True
        self.channel = 963740046995890176
        self.catchannel = 1286439047195004958
        self.send_cat.start()

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS responses
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 question TEXT,
                                 option_1_count INTEGER DEFAULT 0,
                                 option_2_count INTEGER DEFAULT 0)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS user_votes
                                (user_id INTEGER,
                                 question TEXT,
                                 PRIMARY KEY (user_id, question))''')
            await db.commit()

    def cog_unload(self):
        self.post_wyr_question.cancel()
        self.report_results.cancel()

    @tasks.loop(hours=24)
    async def post_wyr_question(self):
        channel = self.bot.get_channel(self.channel)
        wyr_question = await self.get_wyr_question()
        if wyr_question:
            translated_question = self.translator.translate(wyr_question)
            buttons = [
                discord.ui.Button(label="Option 1", style=discord.ButtonStyle.green, custom_id="Option 1"),
                discord.ui.Button(label="Option 2", style=discord.ButtonStyle.red, custom_id="Option 2")]

            view = discord.ui.View(timeout=86400)
            for button in buttons:
                view.add_item(button)

            embed = discord.Embed(title="Würdest du eher:", description=translated_question,
                                  color=discord.Color.green())
            await channel.send(embed=embed, view=view)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO responses (question) VALUES (?)", (translated_question,))
                await db.commit()

            async def button_callback(interaction):
                user_id = interaction.user.id
                question_text = translated_question

                async with aiosqlite.connect(self.db_path) as db:
                    async with db.execute("SELECT * FROM user_votes WHERE user_id = ? AND question = ?",
                                          (user_id, question_text)) as cursor:
                        row = await cursor.fetchone()

                    if row:
                        await interaction.response.send_message("Du hast bereits abgestimmt!", ephemeral=True)
                        return

                    chosen_option = interaction.data['custom_id']
                    await interaction.response.send_message(f"Du hast {chosen_option} gewählt.", ephemeral=True)

                    await db.execute("INSERT INTO user_votes (user_id, question) VALUES (?, ?)",
                                     (user_id, question_text))

                    async with db.execute("SELECT id FROM responses WHERE question = ?",
                                          (question_text,)) as cursor:
                        row = await cursor.fetchone()

                    if row:
                        question_id = row[0]
                        if chosen_option == "Option 1":
                            await db.execute("UPDATE responses SET option_1_count = option_1_count + 1 WHERE id = ?",
                                             (question_id,))
                        else:
                            await db.execute("UPDATE responses SET option_2_count = option_2_count + 1 WHERE id = ?",
                                             (question_id,))
                        await db.commit()

            buttons[0].callback = button_callback
            buttons[1].callback = button_callback

    @post_wyr_question.before_loop
    async def before_post_wyr_question(self):
        await self.bot.wait_until_ready()

    async def get_wyr_question(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.truthordarebot.xyz/api/wyr?rating=pg13') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['question']
                return None

    @tasks.loop(hours=23)
    async def report_results(self):
        channel = self.bot.get_channel(self.channel)

        async with (aiosqlite.connect(self.db_path) as db):
            async with db.execute(
                    "SELECT question, option_1_count, option_2_count FROM responses ORDER BY id DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()

        if row:
            question, option_1_count, option_2_count = row
            total_responses = option_1_count + option_2_count

            if total_responses == 0:
                return

            if self.first_report_skipped:
                self.first_report_skipped = False
            else:
                option_1_percentage = (option_1_count / total_responses) * 100
                option_2_percentage = (option_2_count / total_responses) * 100
                embed = discord.Embed(title="Antwortverteilung für die Frage:", description=question,
                                      color=discord.Color.green())
                embed.add_field(name="Option 1:", value=f"{option_1_percentage:.2f}% ({option_1_count} Stimmen)",
                                inline=True)
                embed.add_field(name="Option 2:", value=f"{option_2_percentage:.2f}% ({option_2_count} Stimmen)",
                                inline=True)
                await channel.send(embed=embed)

    @report_results.before_loop
    async def before_report_results(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def send_cat(self):
        channel = self.bot.get_channel(self.catchannel)  # Setze hier die ID des Forum-Channels ein
        if channel:
            async with aiohttp.ClientSession() as session:
                url = 'https://api.thecatapi.com/v1/images/search'
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        cat_url = data[0]['url']  # Hol die URL des Bildes oder GIFs
                        embed = discord.Embed(title="Daily Dose of Cats! 😺")
                        embed.set_image(url=cat_url)
                        await channel.send(embed=embed)

    @send_cat.before_loop
    async def before_send_cat(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Chat(bot))
