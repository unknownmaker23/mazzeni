import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_file = "data/afk_data.json"
        self.afk_data = self.load_afk()
    
    def load_afk(self):
        if os.path.exists(self.afk_file):
            with open(self.afk_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_afk(self):
        with open(self.afk_file, "w") as f:
            json.dump(self.afk_data, f, indent=4)
    
    @app_commands.command(name="afk", description="Set yourself as AFK (Away From Keyboard)")
    @app_commands.describe(reason="Reason for being AFK (optional)")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Store AFK status per guild
        if guild_id not in self.afk_data:
            self.afk_data[guild_id] = {}
        
        self.afk_data[guild_id][user_id] = {
            "reason": reason,
            "timestamp": discord.utils.utcnow().isoformat(),
            "mentions": 0
        }
        self.save_afk()
        
        await interaction.response.send_message(f"{interaction.user.mention} is now AFK: **{reason}**")
    
    def format_duration(self, afk_time_str):
        """Calculate and format how long user has been AFK"""
        afk_time = datetime.fromisoformat(afk_time_str)
        now = discord.utils.utcnow()
        duration = now - afk_time
        
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours > 0:
                return f"{days}d {hours}h"
            return f"{days}d"
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        
        # Check if user was AFK and is now back
        if guild_id in self.afk_data and user_id in self.afk_data[guild_id]:
            afk_info = self.afk_data[guild_id][user_id]
            mentions = afk_info.get("mentions", 0)
            afk_duration = self.format_duration(afk_info['timestamp'])
            
            del self.afk_data[guild_id][user_id]
            self.save_afk()
            
            if mentions > 0:
                await message.channel.send(
                    f"Welcome back {message.author.mention}! You were AFK for **{afk_duration}** and were mentioned **{mentions}** time(s).",
                    delete_after=10
                )
            else:
                await message.channel.send(
                    f"Welcome back {message.author.mention}! You were AFK for **{afk_duration}**.",
                    delete_after=5
                )
        
        # Check if someone mentioned an AFK user
        for mention in message.mentions:
            mentioned_id = str(mention.id)
            if guild_id in self.afk_data and mentioned_id in self.afk_data[guild_id]:
                afk_info = self.afk_data[guild_id][mentioned_id]
                afk_info["mentions"] = afk_info.get("mentions", 0) + 1
                self.save_afk()
                
                afk_duration = self.format_duration(afk_info['timestamp'])
                
                await message.channel.send(
                    f"{mention.display_name} is AFK: **{afk_info['reason']}** (for {afk_duration})",
                    delete_after=10
                )
    
    @app_commands.command(name="afklist", description="Show all AFK members in this server")
    async def afklist(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        
        if guild_id not in self.afk_data or not self.afk_data[guild_id]:
            await interaction.response.send_message("No one is currently AFK.", ephemeral=True)
            return
        
        afk_members = []
        for user_id, data in self.afk_data[guild_id].items():
            member = interaction.guild.get_member(int(user_id))
            if member:
                afk_duration = self.format_duration(data['timestamp'])
                afk_members.append(f"{member.mention}: {data['reason']} ({afk_duration})")
        
        if not afk_members:
            await interaction.response.send_message("No one is currently AFK.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Currently AFK Members",
            description="\n".join(afk_members),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AFK(bot))
