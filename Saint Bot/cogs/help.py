import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands")
    @app_commands.describe(command="Specific command to get help for (optional)")
    async def help(self, interaction: discord.Interaction, command: str = None):
        if command:
            # Show specific command help
            cmd = self.bot.tree.get_command(command.lower())
            if cmd:
                embed = discord.Embed(
                    title=f"/{cmd.name}",
                    description=cmd.description,
                    color=discord.Color.blue()
                )
                
                # Get parameters
                params = []
                for param in cmd.parameters:
                    required = "Required" if param.required else "Optional"
                    params.append(f"`{param.name}` - {required}")
                
                if params:
                    embed.add_field(name="Parameters", value="\n".join(params), inline=False)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"Command `/{command}` not found.", ephemeral=True)
            return

        # Show all commands
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )

        # Moderation commands
        mod_commands = """
        `/kick <member> [reason]` - Kick a member
        `/ban <member> [reason]` - Ban a member
        `/tempban <member> <minutes> [reason]` - Temporarily ban (auto-unban)
        `/softban <member> [reason]` - Ban+unban (clears messages)
        `/unban <user_id> [reason]` - Unban a user
        `/mute <member> <minutes> [reason]` - Timeout a member
        `/unmute <member> [reason]` - Remove timeout
        `/warn <member> <reason>` - Issue a warning
        `/warnings <member>` - View warnings
        `/note <member> <note>` - Add secret mod note
        `/notes <member>` - View mod notes
        `/role <add/remove> <member> <role>` - Manage roles
        """
        embed.add_field(name="Moderation", value=mod_commands.strip(), inline=False)

        # Channel management
        channel_commands = """
        `/clear <amount>` - Delete messages (1-100)
        `/slowmode <seconds>` - Set slowmode
        `/lockdown <lock/unlock>` - Lock/unlock channel
        `/nuke [name] [count] [message] [msg_count]` - Delete all, create channels with spam
        """
        embed.add_field(name="Channel Management", value=channel_commands.strip(), inline=False)

        # Utility
        utility_commands = """
        `/ping` - Check bot latency
        `/avatar [member]` - Get user's profile picture
        `/userinfo [member]` - View user info (join date, roles, warnings)
        `/serverinfo` - View server stats and boost level
        `/afk [reason]` - Set AFK status
        `/afklist` - View AFK members
        `/help [command]` - Show this help message
        """
        embed.add_field(name="Utility", value=utility_commands.strip(), inline=False)

        # Server Settings
        settings_commands = """
        `/setwelcome <channel>` - Set welcome message channel
        `/setlogs <channel>` - Set join/leave logs channel
        `/setautorole [role]` - Auto-role for new members
        `/setreport <channel>` - Set user reports channel
        `/antilink <enabled>` - Toggle anti-link protection
        """
        embed.add_field(name="Server Settings", value=settings_commands.strip(), inline=False)

        # Extras
        extras_commands = """
        `/report <member> <reason>` - Report user to mods
        `/lockuser <member> [reason]` - Lock user from sending messages
        `/unlockuser <member>` - Unlock user
        `/snipe` - View last deleted message (mod only)
        """
        embed.add_field(name="Extras", value=extras_commands.strip(), inline=False)

        # Admin
        admin_commands = """
        `/backup [name]` - Backup server roles, channels, perms
        `/backups` - List available backups
        `/restore <name> confirm:true` - Restore from backup
        `/bulkdm <role> <message>` - DM all members with role
        """
        embed.add_field(name="Admin", value=admin_commands.strip(), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @help.error
    async def on_help_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
