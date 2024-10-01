import asyncio
import io
from datetime import datetime

import chat_exporter
import discord
import ezcord
from discord.commands import SlashCommandGroup, option


class TicketDB(ezcord.DBHandler):
    def __init__(self):
        super().__init__("database.db")

    async def setup(self):
        try:
            await self.execute(
                """CREATE TABLE IF NOT EXISTS ticket(
                server_id INTEGER PRIMARY KEY,
                category_id INTEGER DEFAULT 0,
                teamrole_id INTEGER DEFAULT 0,
                logs_channel_id INTEGER DEFAULT 0
                )"""
            )
        except Exception as e:
            print(f"Ticket System Fehler beim Datenbank aufsetzen: {e}")

    async def set_category(self, server_id, category_id):
        await self.execute(
            "INSERT INTO ticket (server_id, category_id) VALUES (?, ?) ON CONFLICT(server_id) DO UPDATE SET "
            "category_id = ?",
            (server_id, category_id, category_id)
        )

    async def get_category(self, server_id):
        return await self.one("SELECT category_id FROM ticket WHERE server_id = ?", (server_id,))

    async def set_teamrole(self, server_id, teamrole_id):
        await self.execute(
            "INSERT INTO ticket (server_id, teamrole_id) VALUES (?, ?) ON CONFLICT(server_id) DO UPDATE SET "
            "teamrole_id = ?",
            (server_id, teamrole_id, teamrole_id)
        )

    async def get_teamrole(self, server_id):
        return await self.one("SELECT teamrole_id FROM ticket WHERE server_id = ?", (server_id,))

    async def set_logs_channel(self, server_id, logs_channel_id):
        await self.execute(
            "INSERT INTO ticket (server_id, logs_channel_id) VALUES (?, ?) ON CONFLICT(server_id) DO UPDATE SET "
            "logs_channel_id = ?",
            (server_id, logs_channel_id, logs_channel_id)
        )

    async def get_logs_channel(self, server_id):
        return await self.one("SELECT logs_channel_id FROM ticket WHERE server_id = ?", (server_id,))


db = TicketDB()

options = [
    discord.SelectOption(label="Support", description="Falls du Support brauchst klicke hier", emoji="🎫"),
    discord.SelectOption(label="User Melden", description="Melde einen User", emoji="👥"),
    discord.SelectOption(label="CookieAttack", description="Fragen/BugReport/Reports zu CookieAttack", emoji="🍪"),
]


class Ticket(ezcord.Cog, emoji="🎫"):
    def __init__(self, bot):
        self.bot = bot

    @ezcord.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(0.3)
        print("""          ticket.py          ✅""")
        self.bot.add_view(CreateTicket())
        self.bot.add_view(TicketView())
        self.bot.add_view(CreateTicketSelect())

    ticket = SlashCommandGroup("ticket", default_member_permissions=discord.Permissions(administrator=True))

    @ticket.command(name="setup", description="Create a ticket")
    @discord.guild_only()
    @option("category", description="Select a category", type=discord.CategoryChannel)
    @option("role", description="Select a role", type=discord.Role)
    @option("logs", description="Select a logs Channel", type=discord.TextChannel)
    async def setup_command(self, ctx, category: discord.CategoryChannel, logs: discord.TextChannel,
                            role: discord.Role):
        server_id = ctx.guild.id
        category_id = category.id
        teamrole_id = role.id
        logs_channel_id = logs.id

        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("Nur Admins dürfen diesen Command benutzen.", ephemeral=True)

        await db.set_logs_channel(server_id, logs_channel_id)
        await db.set_category(server_id, category_id)
        await db.set_teamrole(server_id, teamrole_id)

        embed = discord.Embed(
            title="Erstelle ein Ticket",
            description="**Falls du Support brauchst, klicke auf den`📨 Erstelle Ticket` Knopf unten!**",
            color=discord.Color.dark_green()
        )
        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed, view=CreateTicket())
        await ctx.defer(ephemeral=True)
        await ctx.respond("Das Setup wurde erfolgreich beendet.", ephemeral=True)


def setup(bot):
    bot.add_cog(Ticket(bot))


class CreateTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Erstelle Ticket", style=discord.ButtonStyle.primary, emoji="📨", custom_id="create_ticket")
    async def button_callback1(self, button, interaction):
        server_id = interaction.guild.id

        embed = discord.Embed(
            title="Erstelle ein Ticket",
            description="Wählen Sie eine Kategorie aus, um ein Ticket zu erstellen.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=CreateTicketSelect(), ephemeral=True)


class CreateTicketSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="bro_ich_weiss_nicht",
        min_values=1,
        max_values=2,
        placeholder="Wähle eine Kategorie",
        options=options,
    )
    async def ticket_select_callback(self, select, interaction):
        category_id = await db.get_category(interaction.guild.id)
        teamrole_id = await db.get_teamrole(interaction.guild.id)

        if category_id:
            category = discord.utils.get(interaction.guild.categories, id=category_id)

            if category:
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True, read_message_history=True,
                                                                  send_messages=True),
                    interaction.guild.me: discord.PermissionOverwrite(view_channel=True, read_message_history=True,
                                                                      send_messages=True),
                }
                team_role = interaction.guild.get_role(teamrole_id)
                if team_role:
                    topic = f"Ticket für {interaction.user.name}. Kontaktiere {team_role.mention} für hilfe."
                else:
                    topic = f"Ticket für {interaction.user.name}. Kontaktiere Moderatoren für hilfe."

                channel = await category.create_text_channel(name=f"{interaction.user.display_name}",
                                                             overwrites=overwrites, topic=topic)

                msg = await channel.send(
                    f"{team_role.mention if team_role else '@staff'} {interaction.user.mention} hat ein Ticket "
                    f"geöffnet.")
                embed = discord.Embed(
                    title="🎉 Willkommen in unseren Ticket Support! 🎉",
                    description="Bitte beschreibe dein Problem so genau wie möglich ein Moderator/Admin würd sich "
                                "zeitnah darum kümmern.",
                    color=discord.Color.green()
                )

                await channel.send(embed=embed, view=TicketView())
                await interaction.response.send_message(f"Ich habe ein Ticket für dich geöffnet bei {channel.mention}",
                                                        ephemeral=True)
                return

        await interaction.response.send_message(
            "The category ID is not set in the database or the specified category doesn't exist.", ephemeral=True)


options = [
    discord.SelectOption(label="User hinzufügen", description="Füge einen User zum Ticket hinzu", emoji="👥"),
    discord.SelectOption(label="User entfernen", description="Entferne einen User vom Ticket",
                         emoji="<:redcross:758380151238033419>"),
]


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.button_pressed = False

    @discord.ui.button(label="Ticket akzeptiert", style=discord.ButtonStyle.green, emoji="🗂️", row=1,
                       custom_id="accepted_button")
    async def accept_ticket(self, button, interaction):
        team_role_id = await db.get_teamrole(interaction.guild.id)
        if team_role_id is None:
            await interaction.response.send_message(
                "The team role has not been configured. Please contact the administrator.", ephemeral=True)
            return

        team_role = interaction.guild.get_role(team_role_id)
        if team_role is None:
            await interaction.response.send_message(
                "The configured team role was not found. Please contact the administrator.", ephemeral=True)
            return

        if team_role not in interaction.user.roles:
            await interaction.response.send_message("Du hast keine Rechte das Ticket anzunehmen.", ephemeral=True)
            return

        if self.button_pressed:
            await interaction.response.send_message("Das Ticket ist schon akzeptiert.", ephemeral=True)
            return

        await interaction.response.defer()
        member = interaction.user
        embed = discord.Embed(
            title="Ticket akzeptiert",
            description=f"{member.mention} würd sich nun um dich kümmern!",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

        self.button_pressed = True

    @discord.ui.button(label="Schließen", style=discord.ButtonStyle.blurple, emoji="🔐", row=1, custom_id="close_ticket")
    async def close_ticket(self, button, interaction):
        team_role_id = await db.get_teamrole(interaction.guild.id)
        if team_role_id in [role.id for role in interaction.user.roles]:
            server_id = interaction.guild.id

            embed = discord.Embed(
                title="Schließe Ticket",
                description="Lösche Ticket in weniger als `5 Sekunden`... ⏳\n\n"
                            "_Wenn nicht mach es Manuell!_",
                color=discord.Color.dark_red()
            )

            await interaction.response.edit_message(view=self)
            await interaction.followup.send(embed=embed)

            transcript = await chat_exporter.export(interaction.channel)

            if transcript is None:
                return

            transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{interaction.channel.name}.html",
            )
            log_channel_id = await db.get_logs_channel(server_id)
            log_channel = interaction.client.get_channel(log_channel_id)

            message = await log_channel.send(file=transcript_file)
            link = await chat_exporter.link(message)

            topic = interaction.channel.topic
            ticket_owner_name = topic.split("Ticket für ")[1].split(".")[0]

            ticket_owner = discord.utils.get(interaction.guild.members, name=ticket_owner_name)

            if ticket_owner:
                userembed = discord.Embed(
                    title="Dein Ticket wurde geschlossen",
                    description=f"Dein Ticket wurde geschlossen.\n"
                                f"```{interaction.channel.name}```\n"
                                f"Du findest den verlauf [hier]({link}).",
                    color=discord.Color.blue(),
                )
                await ticket_owner.send(embed=userembed)

            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            embed = discord.Embed(
                title="Unbefugt",
                description=f"Du hast keine Rechte Tickets zu schließen.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

    @discord.ui.select(
        custom_id="ticket_actions",
        min_values=1,
        max_values=2,
        placeholder="Wähle eine Aktion",
        options=options,
    )
    async def handle_ticket_actions(self, select, interaction):
        server_id = interaction.guild.id
        teamrole_id = await db.get_teamrole(server_id)

        user_roles = [role.id for role in interaction.user.roles]

        if teamrole_id in user_roles:
            selected_options = interaction.data['values']
            channel = interaction.channel
            await interaction.message.edit(view=self)
            if "User hinzufügen" in selected_options:
                await interaction.response.send_modal(AddUserModal())
            elif "User entfernen" in selected_options:
                await interaction.response.send_modal(RemoveUserModal())


class AddUserModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(
            discord.ui.InputText(
                label="User",
                placeholder="User ID",
                style=discord.InputTextStyle.short,
                custom_id="add_user",
            ),
            title="Füge User zum Ticket hinzu"
        )

    async def callback(self, interaction):
        user = interaction.guild.get_member(int(self.children[0].value))
        if user is None:
            return await interaction.response.send_message("Unbekannter User!",
                                                           ephemeral=True)
        overwrite = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        await interaction.channel.set_permissions(user, overwrite=overwrite)
        await interaction.response.send_message(content=f"{user.mention} wurde zum ticket hinzugefügt!",
                                                ephemeral=True)


class RemoveUserModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(
            discord.ui.InputText(
                label="Remove User",
                placeholder="User ID",
                style=discord.InputTextStyle.short,
                custom_id="remove_user",
            ),
            title="Entferne User vom Ticket"
        )

    async def callback(self, interaction):
        user = interaction.guild.get_member(int(self.children[0].value))
        if user is None:
            return await interaction.response.send_message("Unbekannter User!",
                                                           ephemeral=True)
        overwrite = discord.PermissionOverwrite(view_channel=False, send_messages=False, read_message_history=False)
        await interaction.channel.set_permissions(user, overwrite=overwrite)
        await interaction.response.send_message(content=f"{user.mention} wurde vom Ticket entfernt!",
                                                ephemeral=True)
