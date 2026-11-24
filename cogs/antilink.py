import discord
from discord.ext import commands
from discord import app_commands
import re
import os
import json

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Better regex to detect URLs (http, https, www, discord invites)
        self.url_pattern = re.compile(
            r'(https?://\S+|www\.\S+|discord\.gg/\S+|discord\.com/invite/\S+)',
            re.IGNORECASE
        )
        self.config_file = "data/antilink_config.json"
        self.enabled_guilds = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.enabled_guilds, f, indent=4)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        
        # Check if antilink is enabled for this guild
        if guild_id not in self.enabled_guilds or not self.enabled_guilds[guild_id]:
            return
        
        # Check if user has mod permissions (they can post links)
        if message.author.guild_permissions.manage_messages:
            return
        
        # Check for links
        if self.url_pattern.search(message.content):
            # Delete message
            try:
                await message.delete()
                # Warn user
                await message.channel.send(
                    f"{message.author.mention} Links are not allowed!",
                    delete_after=5
                )
            except:
                pass
    
    @app_commands.command(name="antilink", description="Toggle anti-link protection")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink(self, interaction: discord.Interaction, enabled: bool):
        guild_id = str(interaction.guild_id)
        self.enabled_guilds[guild_id] = enabled
        self.save_config()
        
        await interaction.response.send_message(f"Anti-link {'enabled' if enabled else 'disabled'}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
