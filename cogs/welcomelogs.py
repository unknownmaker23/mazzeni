import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class WelcomeLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/welcome_logs_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)
    
    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {})
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_config = self.get_guild_config(guild_id)
        
        # Welcome message
        welcome_channel_id = guild_config.get("welcome_channel")
        if welcome_channel_id:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                embed = discord.Embed(
                    title="Welcome!",
                    description=f"Welcome {member.mention} to **{member.guild.name}**!\n\n"
                               f"Member #{member.guild.member_count}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"))
                
                # Auto-role if configured
                auto_role_id = guild_config.get("auto_role")
                if auto_role_id:
                    role = member.guild.get_role(auto_role_id)
                    if role:
                        await member.add_roles(role)
                        embed.add_field(name="Role Given", value=role.mention)
                
                await channel.send(embed=embed)
        
        # Join log
        logs_channel_id = guild_config.get("logs_channel")
        if logs_channel_id:
            logs_channel = member.guild.get_channel(logs_channel_id)
            if logs_channel:
                embed = discord.Embed(
                    title="Member Joined",
                    description=f"{member.mention} (`{member.id}`) joined the server.",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await logs_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_config = self.get_guild_config(guild_id)
        
        logs_channel_id = guild_config.get("logs_channel")
        if logs_channel_id:
            logs_channel = member.guild.get_channel(logs_channel_id)
            if logs_channel:
                embed = discord.Embed(
                    title="Member Left",
                    description=f"{member.mention} (`{member.id}`) left the server.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                
                # Show roles they had
                roles = [role.mention for role in member.roles[1:]]
                if roles:
                    embed.add_field(name="Had Roles", value=", ".join(roles[:10]))
                
                await logs_channel.send(embed=embed)
    
    @app_commands.command(name="setwelcome", description="Set the welcome message channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        self.config[guild_id]["welcome_channel"] = channel.id
        self.save_config()
        await interaction.response.send_message(f"Welcome channel set to {channel.mention}")
    
    @app_commands.command(name="setlogs", description="Set the moderation logs channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setlogs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        self.config[guild_id]["logs_channel"] = channel.id
        self.save_config()
        await interaction.response.send_message(f"Logs channel set to {channel.mention}")
    
    @app_commands.command(name="setautorole", description="Set role to give new members (set to none to disable)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setautorole(self, interaction: discord.Interaction, role: discord.Role = None):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        if role:
            self.config[guild_id]["auto_role"] = role.id
            self.save_config()
            await interaction.response.send_message(f"Auto-role set to {role.mention}")
        else:
            if "auto_role" in self.config[guild_id]:
                del self.config[guild_id]["auto_role"]
                self.save_config()
            await interaction.response.send_message("Auto-role disabled")

async def setup(bot):
    await bot.add_cog(WelcomeLogs(bot))
