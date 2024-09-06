import random
import aiosqlite
import discord
from discord import slash_command
from discord.ext import commands
from discord.ui import Button, View

card_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}


def create_deck():
    deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
    random.shuffle(deck)
    return deck


def calculate_hand(hand):
    value = sum(card_values[card] for card in hand)
    if value > 21 and 'A' in hand:
        value -= 10
    return value


class BlackjackView(View):
    def __init__(self, ctx, deck, player_hand, dealer_hand, bet, db, bot):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.bet = bet
        self.db = db
        self.bot = bot

    async def show_hands(self):
        player_value = calculate_hand(self.player_hand)
        dealer_value = calculate_hand(self.dealer_hand[:1])
        embed = discord.Embed(title="Blackjack",
                              description=f"Du hast: {', '.join(self.player_hand)} (Wert: {player_value})\n"
                                          f"Dealer zeigt: {', '.join(self.dealer_hand[:1])} (Wert: {dealer_value})",
                              color=discord.Color.blue())
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Nur der Spieler, der den Befehl ausgeführt hat, kann die Buttons "
                                                    "verwenden!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, button: Button, interaction: discord.Interaction):
        self.player_hand.append(self.deck.pop())
        if calculate_hand(self.player_hand) > 21:
            embed = discord.Embed(title="Verloren", description="Du bist über 21. Du verlierst!",
                                  color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
        else:
            await interaction.response.edit_message(embed=await self.show_hands())

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, button: Button, interaction: discord.Interaction):
        player_value = calculate_hand(self.player_hand)

        while calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())

        dealer_value = calculate_hand(self.dealer_hand)
        embed = discord.Embed(title="Ergebnis",
                              description=f"Dealer hat: {', '.join(self.dealer_hand)} (Wert: {dealer_value})\n"
                                          f"Du hast: {', '.join(self.player_hand)} (Wert: {player_value})",
                              color=discord.Color.blue())

        if dealer_value > 21 or player_value > dealer_value:
            embed.add_field(name="Glückwunsch!", value="Du hast gewonnen!")
            async with aiosqlite.connect(self.db) as db:
                await db.execute("UPDATE users SET cookies = cookies + ? WHERE user_id = ?", (self.bet,
                                                                                              self.ctx.author.id))
                await db.commit()
        elif player_value < dealer_value:
            embed.add_field(name="Schade!", value="Du hast verloren.")
            async with aiosqlite.connect(self.db) as db:
                await db.execute("UPDATE users SET cookies = cookies - ? WHERE user_id = ?", (self.bet,
                                                                                              self.ctx.author.id))
                await db.commit()
        else:
            embed.add_field(name="Unentschieden!", value="Niemand hat gewonnen.")

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = "database.db"

    @commands.Cog.listener()
    async def on_ready(self):
        print("              blackjack.py     ✅")

    @slash_command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int):
        async with aiosqlite.connect(self.db) as db:
            async with db.execute("SELECT cookies FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    embed = discord.Embed(title="Fehler", description="Du hast noch keine Cookies!",
                                          color=discord.Color.red())
                    await ctx.respond(embed=embed, ephemeral=True)
                    return print(f"{ctx.author} hat noch keine Cookies und wollte Blackjack spielen!")
                if result[0] < bet:
                    embed = discord.Embed(title="Fehler", description=f"Du hast nur {result[0]} Cookies!",
                                          color=discord.Color.red())
                    await ctx.respond(embed=embed, ephemeral=True)
                    return print(f"{ctx.author} hat nicht genug Cookies und wollte Blackjack spielen!")
                if bet < 1:
                    embed = discord.Embed(title="Fehler", description="Du musst mindestens 1 Cookie setzen!",
                                          color=discord.Color.red())
                    await ctx.respond(embed=embed, ephemeral=True)
                    return print(f"{ctx.author} wollte weniger als 1 Cookie setzen!")
                if bet > 1000:
                    embed = discord.Embed(title="Fehler", description="Du kannst maximal 1000 Cookies setzen!",
                                          color=discord.Color.red())
                    await ctx.respond(embed=embed, ephemeral=True)
                    return print(f"{ctx.author} wollte mehr als 1000 Cookies setzen!")

            deck = create_deck()
            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]

            view = BlackjackView(ctx, deck, player_hand, dealer_hand, bet, self.db, self.bot)
            await ctx.respond(embed=await view.show_hands(), view=view)


def setup(bot):
    bot.add_cog(Blackjack(bot))
