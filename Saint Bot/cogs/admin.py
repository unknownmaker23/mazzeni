import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = "data/backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def sanitize_filename(self, name):
        """Prevent path traversal attacks"""
        import re
        return re.sub(r'[^\w\-_\.]', '_', name)
    
    @app_commands.command(name="backup", description="Backup server roles, channels, and permissions")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction, name: str = None):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        if name:
            name = self.sanitize_filename(name)
        backup_name = name or datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"{guild.id}_{backup_name}.json")
        
        backup_data = {
            "name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "guild_name": guild.name,
            "guild_id": guild.id,
            "roles": [],
            "channels": [],
            "categories": []
        }
        
        # Backup roles (excluding @everyone)
        for role in guild.roles:
            if role.name != "@everyone":
                backup_data["roles"].append({
                    "name": role.name,
                    "color": role.color.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "permissions": role.permissions.value,
                    "position": role.position
                })
        
        # Backup categories first
        for category in guild.categories:
            cat_data = {
                "name": category.name,
                "position": category.position,
                "channels": []
            }
            backup_data["categories"].append(cat_data)
        
        # Backup channels
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                ch_data = {
                    "name": channel.name,
                    "type": "text",
                    "position": channel.position,
                    "slowmode_delay": channel.slowmode_delay,
                    "nsfw": channel.nsfw,
                    "category": channel.category.name if channel.category else None,
                    "overwrites": []
                }
                # Save permission overwrites
                for target, perm in channel.overwrites.items():
                    ch_data["overwrites"].append({
                        "target": target.name,
                        "target_type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": perm[0].value if perm[0] else 0,
                        "deny": perm[1].value if perm[1] else 0
                    })
                backup_data["channels"].append(ch_data)
            
            elif isinstance(channel, discord.VoiceChannel):
                ch_data = {
                    "name": channel.name,
                    "type": "voice",
                    "position": channel.position,
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit,
                    "category": channel.category.name if channel.category else None,
                    "overwrites": []
                }
                for target, perm in channel.overwrites.items():
                    ch_data["overwrites"].append({
                        "target": target.name,
                        "target_type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": perm[0].value if perm[0] else 0,
                        "deny": perm[1].value if perm[1] else 0
                    })
                backup_data["channels"].append(ch_data)
        
        # Save to file
        with open(backup_file, "w") as f:
            json.dump(backup_data, f, indent=2)
        
        role_count = len(backup_data["roles"])
        channel_count = len(backup_data["channels"])
        cat_count = len(backup_data["categories"])
        
        await interaction.followup.send(
            f"Backup created: {backup_name}\n"
            f"Roles: {role_count}, Channels: {channel_count}, Categories: {cat_count}",
            ephemeral=True
        )
    
    @app_commands.command(name="backups", description="List all available backups")
    @app_commands.checks.has_permissions(administrator=True)
    async def backups(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        backup_files = []
        for f in os.listdir(self.backup_dir):
            if f.startswith(f"{guild_id}_") and f.endswith(".json"):
                backup_name = f.replace(f"{guild_id}_", "").replace(".json", "")
                backup_files.append(backup_name)
        
        if not backup_files:
            await interaction.response.send_message("No backups found.", ephemeral=True)
            return
        
        embed = discord.Embed(title="Available Backups")
        for backup_name in backup_files[:10]:  # Show max 10
            embed.add_field(name=backup_name, value="Use /restore with this name", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="restore", description="Restore server from backup")
    @app_commands.checks.has_permissions(administrator=True)
    async def restore(self, interaction: discord.Interaction, name: str, confirm: bool = False):
        name = self.sanitize_filename(name)
        
        if not confirm:
            await interaction.response.send_message(
                f"WARNING: This will delete existing channels and recreate them.\n"
                f"Type: `/restore name:{name} confirm:true` to confirm.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        backup_file = os.path.join(self.backup_dir, f"{guild.id}_{name}.json")
        
        if not os.path.exists(backup_file):
            await interaction.followup.send("Backup not found.", ephemeral=True)
            return
        
        with open(backup_file, "r") as f:
            backup_data = json.load(f)
        
        # Delete existing channels (except system channels)
        for channel in guild.channels:
            if channel != guild.system_channel and not isinstance(channel, discord.CategoryChannel):
                try:
                    await channel.delete()
                except:
                    pass
        
        # Create categories first
        category_map = {}
        for cat_data in backup_data.get("categories", []):
            try:
                category = await guild.create_category(name=cat_data["name"])
                category_map[cat_data["name"]] = category
            except:
                pass
        
        # Create channels
        for ch_data in backup_data.get("channels", []):
            try:
                category = category_map.get(ch_data.get("category"))
                
                if ch_data["type"] == "text":
                    await guild.create_text_channel(
                        name=ch_data["name"],
                        category=category,
                        slowmode_delay=ch_data.get("slowmode_delay", 0),
                        nsfw=ch_data.get("nsfw", False)
                    )
                elif ch_data["type"] == "voice":
                    await guild.create_voice_channel(
                        name=ch_data["name"],
                        category=category,
                        bitrate=ch_data.get("bitrate", 64000),
                        user_limit=ch_data.get("user_limit", 0)
                    )
            except:
                pass
        
        await interaction.followup.send("Restore completed. Roles and permissions not restored for safety.", ephemeral=True)
    
    @app_commands.command(name="bulkdm", description="DM all members with a specific role")
    @app_commands.checks.has_permissions(administrator=True)
    async def bulkdm(self, interaction: discord.Interaction, role: discord.Role, message: str):
        await interaction.response.defer(ephemeral=True)
        
        members = role.members
        success_count = 0
        fail_count = 0
        
        for member in members:
            if member.bot:
                continue
            try:
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"From {interaction.guild.name}")
                await member.send(embed=embed)
                success_count += 1
                await asyncio.sleep(1)  # Rate limit protection
            except:
                fail_count += 1
        
        await interaction.followup.send(
            f"Bulk DM sent:\n"
            f"Success: {success_count}\n"
            f"Failed: {fail_count}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Admin(bot))
