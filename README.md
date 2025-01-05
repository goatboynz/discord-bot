# Discord Server Builder Bot 🤖

A powerful Discord bot that helps you create and manage server structures using AI-powered generation. The bot can create channels, roles, and content automatically based on your descriptions.

## Features 🌟

### Server Structure Creation
- **Automated Setup**: Create a complete server structure with a single command
- **AI-Generated Content**: Uses Gemini AI to generate appropriate channels, roles, and content
- **Smart Organization**: Automatically organizes channels into categories
- **Permission Management**: Sets up proper permissions for roles and channels

### Commands

#### Main Commands
1. `!build_server <description>`
   - Creates a complete server structure based on your description
   - Example: `!build_server Create a gaming community server focused on Minecraft`

2. `!add <type> <description>`
   - Add new content to your server
   - Types:
     - `channels`: Create new channels
     - `roles`: Create new roles
     - `content`: Add content to existing channels
   - Examples:
     ```
     !add channels Create a support section with help-desk
     !add roles Create roles for different game teams
     !add content Create detailed server rules
     ```

### Channel Types
- **Text Channels**: For text-based communication
- **Voice Channels**: For voice chat and gaming sessions
- **Forum Channels**: For community discussions and topics

### Role Management
- **Hierarchical Roles**: Creates roles with proper permissions
- **Custom Colors**: Assigns unique colors to roles
- **Permission Settings**: Sets appropriate permissions for each role

## Initial Setup and Bot Invitation 🔑

### 1. Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under the bot's username, click "Reset Token" and copy your token
   - ⚠️ Keep this token secret! Never share it publicly

### 2. Configure Bot Settings
1. In the Bot section, enable these options:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
2. Under "Bot Permissions", check:
   - ✅ Administrator (Required for server management)

### 3. Create Invite Link
1. Go to "OAuth2" → "URL Generator"
2. Select these scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under "Bot Permissions" select:
   - ✅ Administrator
4. Copy the generated URL at the bottom

### 4. Invite Bot to Server
1. Open the generated URL in a web browser
2. Select your server from the dropdown
3. Click "Continue"
4. Review permissions (should show Administrator)
5. Click "Authorize"
6. Complete the CAPTCHA if prompted

### 5. Configure Environment
1. Create a `.env` file in the bot directory:
   ```
   DISCORD_TOKEN=your_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
2. Replace `your_bot_token_here` with the token from step 1
3. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
4. Replace `your_gemini_api_key_here` with your Gemini API key

### 6. Start the Bot
1. Open a terminal in the bot directory
2. Run:
   ```bash
   python bot.py
   ```
3. You should see "Bot is ready!" in the console
4. The bot will create a `bot-commands` channel in your server

### Troubleshooting 🔧

If the bot isn't working:

1. **Bot Not Responding**
   - Check if the bot is online in your server
   - Verify the token in `.env` is correct
   - Make sure all intents are enabled in the Developer Portal

2. **Permission Errors**
   - Verify the bot role is at the top of the role list
   - Check if the bot has Administrator permission
   - Try removing and reinviting the bot

3. **Command Errors**
   - Use commands in the `bot-commands` channel
   - Make sure you have Administrator permission
   - Check the console for error messages

## Setup 🔧

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   DISCORD_TOKEN=your_discord_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. Invite the bot to your server with Administrator permissions

## Usage Examples 💡

### Creating a Gaming Server
```
!build_server Create a gaming community server focused on Minecraft and other games, with separate areas for different games, voice channels for gaming sessions, streaming areas, community forums, role-based access for different games, and special roles for moderators and event organizers
```

### Adding Rules
```
!add content Create comprehensive rules for a gaming community that focuses on fair play and respect
```

### Adding Game Channels
```
!add channels Create channels for Minecraft including general chat, building showcase, and survival discussion
```

## Features in Detail 📝

### AI-Powered Generation
- Uses Gemini AI for intelligent content generation
- Creates contextually appropriate channel names
- Generates well-formatted server rules and information
- Designs role hierarchies based on server needs

### Channel Management
- Creates channels in appropriate categories
- Sets up proper permissions
- Adds channel topics and descriptions
- Supports text, voice, and forum channels

### Role System
- Creates roles with custom colors
- Sets up permission hierarchies
- Makes roles mentionable when appropriate
- Organizes roles for easy management

### Content Generation
- Creates formatted rules with sections
- Generates welcome messages
- Sets up announcement templates
- Uses Discord markdown for beautiful formatting

## Best Practices 🎯

1. **Start with a Clear Plan**
   - Describe your server purpose clearly
   - Include all major features you want
   - Specify any special requirements

2. **Add Content Gradually**
   - Create basic structure first
   - Add specific rules and information
   - Fine-tune roles and permissions

3. **Review and Adjust**
   - Check generated content
   - Adjust permissions if needed
   - Add more specific channels or roles

## Support 🆘

If you encounter any issues or need help:
1. Use the `bot-commands` channel for bot interactions
2. Make sure the bot has administrator permissions
3. Check the error messages for specific issues

## Support the Project 💝

If you find this bot helpful and want to support its development, you can make a donation! Your support helps maintain and improve the bot.

### Donate via PayPal
[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue.svg)](https://paypal.me/kiwidabman)

- Email: kiwidabman@gmail.com
- Link: [PayPal.me/kiwidabman](https://paypal.me/kiwidabman)

Your donations help:
- 🚀 Keep the bot running 24/7
- 💻 Develop new features
- 🛠️ Maintain and improve existing features
- 📚 Create better documentation

### Supporters
We appreciate all our supporters! Donors will be acknowledged here (with permission).

## Note ⚠️

- The bot requires administrator permissions
- Some operations may take a few moments to complete
- Always review generated content and adjust if needed
