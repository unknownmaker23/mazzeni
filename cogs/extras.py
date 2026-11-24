import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/extras_config.json"
        self.config = self.load_config()
        self.snipe_cache = {}  # channel_id: last_deleted_message
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)
    
    @app_commands.command(name="report", description="Report a user to moderators")
    @app_commands.describe(member="User to report", reason="Reason for report")
    async def report(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        guild_id = str(interaction.guild_id)
        report_channel_id = self.config.get(guild_id, {}).get("report_channel")
        
        if not report_channel_id:
            await interaction.response.send_message("Report channel not set. Ask admin to use /setreport", ephemeral=True)
            return
        
        report_channel = interaction.guild.get_channel(report_channel_id)
        if not report_channel:
            await interaction.response.send_message("Report channel not found.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="User Report",
            description=f"Reporter: {interaction.user.mention}\nReported: {member.mention}\nReason: {reason}",
            color=discord.Color.orange()
        )
        await report_channel.send(embed=embed)
        await interaction.response.send_message("Report sent to moderators.", ephemeral=True)
    
    @app_commands.command(name="setreport", description="Set channel for user reports")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setreport(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]["report_channel"] = channel.id
        self.save_config()
        await interaction.response.send_message(f"Report channel set to {channel.mention}", ephemeral=True)
    
    @app_commands.command(name="lockuser", description="Prevent user from sending messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def lockuser(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        for channel in interaction.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(member, send_messages=False)
        
        msg = f"Locked {member.mention}"
        if reason:
            msg += f". {reason}"
        await interaction.response.send_message(msg)
    
    @app_commands.command(name="unlockuser", description="Allow user to send messages again")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unlockuser(self, interaction: discord.Interaction, member: discord.Member):
        for channel in interaction.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(member, send_messages=None)
        
        await interaction.response.send_message(f"Unlocked {member.mention}")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        self.snipe_cache[message.channel.id] = {
            "content": message.content,
            "author": message.author,
            "time": discord.utils.utcnow()
        }
    
    @app_commands.command(name="snipe", description="Show last deleted message")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def snipe(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        if channel_id not in self.snipe_cache:
            await interaction.response.send_message("No deleted messages found.", ephemeral=True)
            return
        
        data = self.snipe_cache[channel_id]
        embed = discord.Embed(
            description=data["content"] or "(empty message)",
            color=discord.Color.greyple()
        )
        embed.set_author(name=str(data["author"]), icon_url=data["author"].display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Extras(bot))
