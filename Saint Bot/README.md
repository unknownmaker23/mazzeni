# Discord Moderation Bot

A simple Discord bot with moderation commands.

## Commands

- `/kick <member> [reason]` - Kick a member from the server
- `/ban <member> [reason]` - Ban a member from the server
- `/mute <member> <duration_minutes> [reason]` - Timeout/mute a member
- `/role <add|remove> <member> <role>` - Add or remove a role from a member

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create New Application → Bot → Add Bot
   - Enable "Server Members Intent" and "Message Content Intent"
   - Copy the bot token

3. Replace `YOUR_BOT_TOKEN_HERE` in `bot.py` with your actual token

4. Invite bot to your server with permissions:
   - Kick Members
   - Ban Members
   - Moderate Members
   - Manage Roles
   - Send Messages
   - Use Slash Commands

5. Run the bot:
```
python bot.py
```

## Requirements

- Python 3.8+
- discord.py 2.3.0+
