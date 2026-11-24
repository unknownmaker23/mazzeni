import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "warnings.json"

    def load_warnings(self):
        if os.path.exists(self.warnings_file):
            with open(self.warnings_file, "r") as f:
                return json.load(f)
        return {}

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="Pong!",
            description=f"Latency: **{latency}ms**",
            color=discord.Color.green() if latency < 200 else discord.Color.orange() if latency < 500 else discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="avatar", description="Get user's profile picture")
    @app_commands.describe(member="The member (leave empty for yourself)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        embed = discord.Embed(
            title=f"{target}'s Avatar",
            color=discord.Color.blue()
        )
        
        # Show different avatar sizes
        avatar_url = target.display_avatar.url
        embed.set_image(url=avatar_url)
        
        # Add links
        formats = ["png", "jpg", "webp"]
        links = []
        for fmt in formats:
            url = target.display_avatar.with_format(fmt).url
            links.append(f"[{fmt.upper()}]({url})")
        
        embed.description = " | ".join(links)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="View user information")
    @app_commands.describe(member="The member (leave empty for yourself)")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        embed = discord.Embed(
            title=f"User Info: {target}",
            color=target.color
        )
        
        # Avatar
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Basic info
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
        embed.add_field(name="Bot", value="Yes" if target.bot else "No", inline=True)
        
        # Dates
        created_at = target.created_at.strftime("%B %d, %Y")
        joined_at = target.joined_at.strftime("%B %d, %Y") if target.joined_at else "Unknown"
        
        embed.add_field(name="Account Created", value=created_at, inline=True)
        embed.add_field(name="Joined Server", value=joined_at, inline=True)
        
        # Roles (excluding @everyone)
        roles = [role.mention for role in target.roles[1:]]  # Skip @everyone
        if roles:
            roles_str = ", ".join(roles) if len(", ".join(roles)) < 1024 else ", ".join(roles[:10]) + f"... ({len(roles)} total)"
            embed.add_field(name=f"Roles ({len(roles)})", value=roles_str, inline=False)
        else:
            embed.add_field(name="Roles", value="None", inline=False)
        
        # Highest role color
        if target.color.value != 0:
            embed.color = target.color
        
        # Get warnings count
        guild_id = str(interaction.guild_id)
        user_id = str(target.id)
        warnings = self.load_warnings().get(guild_id, {}).get(user_id, [])
        warning_count = len(warnings)
        
        embed.add_field(name="Warnings", value=str(warning_count), inline=True)
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="View server statistics")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"Server Info: {guild.name}",
            color=discord.Color.blue()
        )
        
        # Server icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic stats
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        
        # Member stats
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total_members - humans
        
        embed.add_field(name="Total Members", value=str(total_members), inline=True)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        
        # Channel stats
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=str(text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=str(voice_channels), inline=True)
        embed.add_field(name="Categories", value=str(categories), inline=True)
        
        # Boost info
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        
        embed.add_field(name="Boost Level", value=f"Level {boost_level}", inline=True)
        embed.add_field(name="Boosts", value=f"{boost_count} boosts", inline=True)
        
        # Roles and emojis
        embed.add_field(name="Roles", value=f"{len(guild.roles)} roles", inline=True)
        embed.add_field(name="Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit} emojis", inline=True)
        
        # Features
        if guild.features:
            features = ", ".join([f.replace("_", " ").title() for f in guild.features[:5]])
            embed.add_field(name="Features", value=features, inline=False)
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)

    @ping.error
    @avatar.error
    @userinfo.error
    @serverinfo.error
    async def on_utility_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
