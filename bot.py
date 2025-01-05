import os
import json
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
from typing import Optional

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Configure Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

async def ensure_bot_role(ctx):
    """Ensure the bot has its own role with necessary permissions"""
    guild = ctx.guild
    bot_member = guild.me
    
    # Define bot role permissions
    bot_permissions = discord.Permissions(
        administrator=True,  # This ensures the bot can perform all operations
        manage_guild=True,
        manage_roles=True,
        manage_channels=True,
        manage_messages=True,
        manage_webhooks=True,
        read_messages=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        mention_everyone=True,
        use_external_emojis=True,
        add_reactions=True,
        connect=True,
        speak=True,
        mute_members=True,
        deafen_members=True,
        move_members=True,
        use_voice_activation=True,
        create_instant_invite=True,
        manage_nicknames=True,
        manage_emojis=True,
        view_audit_log=True,
        kick_members=True,
        ban_members=True
    )

    # Check if bot already has a role
    bot_role = discord.utils.get(guild.roles, name="🤖 Server Builder")
    
    if not bot_role:
        # Create new role for bot
        try:
            bot_role = await guild.create_role(
                name="🤖 Server Builder",
                permissions=bot_permissions,
                color=discord.Color.blue(),
                hoist=True,
                mentionable=True,
                reason="Bot role creation"
            )
            await ctx.send("✅ Created bot role with necessary permissions")
        except Exception as e:
            await ctx.send(f"❌ Failed to create bot role: {str(e)}")
            return None
    
    # Ensure the bot has this role
    if bot_role not in bot_member.roles:
        try:
            await bot_member.add_roles(bot_role)
            await ctx.send("✅ Assigned bot role to bot")
        except Exception as e:
            await ctx.send(f"❌ Failed to assign bot role: {str(e)}")
            return None
    
    # Move bot role to top (just below server owner)
    try:
        positions = {role: role.position for role in guild.roles}
        positions[bot_role] = max(role.position for role in guild.roles if role.name != "@everyone") - 1
        await guild.edit_role_positions(positions=positions)
        await ctx.send("✅ Positioned bot role correctly")
    except Exception as e:
        await ctx.send(f"⚠️ Failed to position bot role: {str(e)}")
    
    return bot_role

async def create_bot_channel(ctx):
    """Create a dedicated channel for bot commands if it doesn't exist"""
    guild = ctx.guild
    
    # Check if bot channel already exists
    existing_channel = discord.utils.get(guild.channels, name="bot-commands")
    if existing_channel:
        return existing_channel
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
    }
    
    bot_channel = await guild.create_text_channel(
        'bot-commands',
        overwrites=overwrites,
        topic="Channel for bot commands and server setup",
        reason="Bot setup channel"
    )
    return bot_channel

async def clean_server(ctx, preserve_bot=True):
    """Remove all existing channels and roles while preserving bot role and channel"""
    guild = ctx.guild
    bot_role = discord.utils.get(guild.roles, name="🤖 Server Builder")
    bot_channel = discord.utils.get(guild.channels, name="bot-commands")
    
    # Delete all channels except bot channel if preserve_bot is True
    await ctx.send("🧹 Cleaning up existing channels...")
    for channel in guild.channels:
        if preserve_bot and channel == bot_channel:
            continue
        try:
            await channel.delete()
            await asyncio.sleep(0.5)  # Avoid rate limits
        except discord.Forbidden:
            await ctx.send(f"⚠️ Cannot delete channel: {channel.name}")
        except Exception as e:
            await ctx.send(f"Error deleting channel {channel.name}: {str(e)}")
    
    # Delete all roles except @everyone and bot role if preserve_bot is True
    await ctx.send("🧹 Cleaning up existing roles...")
    preserved_roles = {"@everyone"}
    if preserve_bot:
        preserved_roles.add("🤖 Server Builder")
    
    for role in guild.roles:
        if role.name not in preserved_roles:
            try:
                await role.delete()
                await asyncio.sleep(0.5)  # Avoid rate limits
            except discord.Forbidden:
                await ctx.send(f"⚠️ Cannot delete role: {role.name}")
            except Exception as e:
                await ctx.send(f"Error deleting role {role.name}: {str(e)}")
    
    return True

async def cleanup_bot_resources(ctx):
    """Clean up bot's role and channel"""
    guild = ctx.guild
    bot_role = discord.utils.get(guild.roles, name="🤖 Server Builder")
    bot_channel = discord.utils.get(guild.channels, name="bot-commands")
    
    if bot_channel:
        try:
            await bot_channel.delete()
            await asyncio.sleep(0.5)
        except Exception as e:
            await ctx.send(f"⚠️ Could not delete bot channel: {str(e)}")
    
    if bot_role:
        try:
            await bot_role.delete()
            await asyncio.sleep(0.5)
        except Exception as e:
            await ctx.send(f"⚠️ Could not delete bot role: {str(e)}")

async def create_server_structure(ctx, server_plan):
    """Create channels, roles, and configure server based on the plan"""
    try:
        guild = ctx.guild
        await ctx.send("🚀 Starting server configuration...")
        
        # Clean up existing channels and roles first
        await ctx.send("🧹 Cleaning up existing server structure...")
        try:
            await clean_server(ctx, preserve_bot=True)
            await ctx.send("✅ Cleanup completed")
        except Exception as e:
            await ctx.send(f"⚠️ Error during cleanup: {str(e)}")
            await ctx.send("Would you like to continue anyway? (yes/no)")
            try:
                msg = await bot.wait_for('message', timeout=30.0, 
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                if msg.content.lower() == 'no':
                    return False
            except asyncio.TimeoutError:
                await ctx.send("No response received, stopping setup.")
                return False
        
        # Create roles first (to use in channel permissions)
        await ctx.send("👥 Creating roles...")
        roles_map = {}  # Store created roles for permission setup
        for role_data in server_plan['roles']:
            try:
                role = await guild.create_role(
                    name=role_data['name'],
                    color=discord.Color.from_str(role_data['color']),
                    hoist=role_data['hoist'],
                    mentionable=role_data['mentionable'],
                    permissions=discord.Permissions(**role_data['permissions'])
                )
                roles_map[role_data['name']] = role
                await ctx.send(f"✅ Created role: {role.name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                await ctx.send(f"⚠️ Error creating role {role_data['name']}: {str(e)}")
                await ctx.send("Would you like to continue with the next role? (yes/no)")
                try:
                    msg = await bot.wait_for('message', timeout=30.0, 
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                    if msg.content.lower() == 'no':
                        return False
                    continue
                except asyncio.TimeoutError:
                    await ctx.send("No response received, stopping setup.")
                    return False
        
        # Create categories and channels
        await ctx.send("📁 Creating categories and channels...")
        for category_data in server_plan['categories']:
            try:
                # Set up category permissions
                overwrites = {}
                if 'permissions' in category_data:
                    for role_name, perms in category_data['permissions'].items():
                        if role_name in roles_map:
                            overwrites[roles_map[role_name]] = discord.PermissionOverwrite(**perms)
                
                # Create category
                category = await guild.create_category(
                    name=category_data['name'],
                    overwrites=overwrites,
                    position=category_data['position']
                )
                await ctx.send(f"✅ Created category: {category.name}")
                await asyncio.sleep(0.5)
                
                # Create channels in category
                for channel_data in category_data.get('channels', []):
                    try:
                        channel_type = channel_data['type'].lower()
                        channel_overwrites = overwrites.copy()
                        
                        # Add channel-specific permission overwrites
                        if 'permissions' in channel_data:
                            for role_name, perms in channel_data['permissions'].items():
                                if role_name in roles_map:
                                    channel_overwrites[roles_map[role_name]] = discord.PermissionOverwrite(**perms)
                        
                        try:
                            if channel_type == 'text':
                                await category.create_text_channel(
                                    name=channel_data['name'],
                                    topic=channel_data.get('topic', ''),
                                    slowmode_delay=channel_data.get('slowmode_delay', 0),
                                    nsfw=channel_data.get('nsfw', False),
                                    overwrites=channel_overwrites,
                                    position=channel_data.get('position', 0)
                                )
                            elif channel_type == 'voice':
                                await category.create_voice_channel(
                                    name=channel_data['name'],
                                    overwrites=channel_overwrites,
                                    position=channel_data.get('position', 0)
                                )
                            elif channel_type == 'forum':
                                await category.create_forum(
                                    name=channel_data['name'],
                                    topic=channel_data.get('topic', ''),
                                    overwrites=channel_overwrites,
                                    position=channel_data.get('position', 0)
                                )
                            await ctx.send(f"✅ Created {channel_type} channel: {channel_data['name']}")
                        except Exception as e:
                            await ctx.send(f"⚠️ Error creating {channel_type} channel {channel_data['name']}: {str(e)}")
                            await ctx.send("Would you like to continue with the next channel? (yes/no)")
                            try:
                                msg = await bot.wait_for('message', timeout=30.0, 
                                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                                if msg.content.lower() == 'no':
                                    return False
                                continue
                            except asyncio.TimeoutError:
                                await ctx.send("No response received, stopping setup.")
                                return False
                        
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        await ctx.send(f"⚠️ Error with channel {channel_data['name']}: {str(e)}")
                        await ctx.send("Would you like to continue with the next channel? (yes/no)")
                        try:
                            msg = await bot.wait_for('message', timeout=30.0, 
                                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                            if msg.content.lower() == 'no':
                                return False
                            continue
                        except asyncio.TimeoutError:
                            await ctx.send("No response received, stopping setup.")
                            return False
                        
            except Exception as e:
                await ctx.send(f"⚠️ Error creating category {category_data['name']}: {str(e)}")
                await ctx.send("Would you like to continue with the next category? (yes/no)")
                try:
                    msg = await bot.wait_for('message', timeout=30.0, 
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                    if msg.content.lower() == 'no':
                        return False
                    continue
                except asyncio.TimeoutError:
                    await ctx.send("No response received, stopping setup.")
                    return False
        
        # Update server settings
        if 'server_config' in server_plan:
            try:
                await ctx.send("⚙️ Updating server settings...")
                await guild.edit(
                    name=server_plan['server_config']['name'],
                    verification_level=discord.VerificationLevel(server_plan['server_config']['verification_level']),
                    explicit_content_filter=discord.ContentFilter(server_plan['server_config']['explicit_content_filter']),
                    afk_timeout=server_plan['server_config']['afk_timeout']
                )
                await ctx.send("✅ Server settings updated")
            except Exception as e:
                await ctx.send(f"⚠️ Error updating server settings: {str(e)}")
                await ctx.send("Would you like to continue anyway? (yes/no)")
                try:
                    msg = await bot.wait_for('message', timeout=30.0, 
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                    if msg.content.lower() == 'no':
                        return False
                except asyncio.TimeoutError:
                    await ctx.send("No response received, stopping setup.")
                    return False
        
        await ctx.send("✨ Server structure creation completed!")
        
        # Ask about additional changes
        while True:
            await ctx.send("Would you like to make any additional changes? Choose an option:\n1. Add more channels\n2. Add more roles\n3. Add channel content (rules, info, etc.)\n4. No more changes (done)")
            try:
                msg = await bot.wait_for('message', timeout=30.0, 
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ['1', '2', '3', '4'])
                
                if msg.content == '1':
                    await ctx.send("Please describe the additional channels you'd like to add:")
                    desc = await bot.wait_for('message', timeout=60.0, 
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                    # Generate and add new channels using AI
                    new_channels = await generate_channels(desc.content)
                    # Add the new channels to existing categories
                    await add_channels(ctx, new_channels, roles_map)
                
                elif msg.content == '2':
                    await ctx.send("Please describe the additional roles you'd like to add:")
                    desc = await bot.wait_for('message', timeout=60.0, 
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                    # Generate and add new roles using AI
                    new_roles = await generate_roles(desc.content)
                    await add_roles(ctx, new_roles)
                
                elif msg.content == '3':
                    # Ask about adding content to specific channels
                    channels = [c for c in ctx.guild.channels if isinstance(c, discord.TextChannel)]
                    channel_list = "\n".join([f"{i+1}. {c.name}" for i, c in enumerate(channels)])
                    await ctx.send(f"Which channel would you like to add content to? (enter the number)\n{channel_list}\n{len(channels)+1}. Done adding content")
                    
                    while True:
                        try:
                            msg = await bot.wait_for('message', timeout=30.0, 
                                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(channels)+1)
                            
                            if int(msg.content) == len(channels)+1:
                                break
                                
                            selected_channel = channels[int(msg.content)-1]
                            await ctx.send(f"What content would you like to add to #{selected_channel.name}? (type your content or 'skip' to skip)")
                            content = await bot.wait_for('message', timeout=120.0, 
                                check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                            
                            if content.content.lower() != 'skip':
                                # Generate formatted content using AI
                                formatted_content = await generate_channel_content(selected_channel.name, content.content)
                                await selected_channel.send(formatted_content)
                                await ctx.send(f"✅ Content added to #{selected_channel.name}")
                            
                            await ctx.send("Would you like to add content to another channel? (yes/no)")
                            continue_resp = await bot.wait_for('message', timeout=30.0, 
                                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
                            if continue_resp.content.lower() == 'no':
                                break
                                
                        except asyncio.TimeoutError:
                            await ctx.send("No response received, skipping content addition")
                            break
                
                elif msg.content == '4':
                    break
                    
            except asyncio.TimeoutError:
                await ctx.send("No response received, moving on")
                break
        
        # Ask about cleanup at the very end
        await ctx.send("🧹 Would you like me to clean up the bot's channel and role? (yes/no)")
        try:
            msg = await bot.wait_for('message', timeout=30.0, 
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
            if msg.content.lower() == 'yes':
                await clean_server(ctx, preserve_bot=False)
                await ctx.send("✅ Cleanup completed")
            else:
                await ctx.send("Keeping bot's channel and role")
        except asyncio.TimeoutError:
            await ctx.send("No response received, keeping bot's channel and role")
        
        return True
        
    except Exception as e:
        await ctx.send(f"❌ An unexpected error occurred: {str(e)}")
        await ctx.send("Would you like to try continuing? (yes/no)")
        try:
            msg = await bot.wait_for('message', timeout=30.0, 
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'])
            if msg.content.lower() == 'yes':
                return True
            return False
        except asyncio.TimeoutError:
            await ctx.send("No response received, stopping setup.")
            return False

@bot.command(name='build_server')
@commands.has_permissions(administrator=True)
async def build_server(ctx, *, description):
    """Build a server based on the provided description"""
    try:
        # Log the start of the command
        print(f"Starting build_server command in channel {ctx.channel.name} ({ctx.channel.id})")
        
        # Create or get bot role first
        try:
            bot_role = await ensure_bot_role(ctx)
            if not bot_role:
                print("Failed to create/get bot role")
                return
            print("Bot role setup successful")
        except Exception as e:
            await ctx.send(f"❌ Error during bot role setup: {str(e)}")
            print(f"Bot role error: {str(e)}")
            return
            
        # Create or get bot channel
        try:
            bot_channel = await create_bot_channel(ctx)
            if not bot_channel:
                print("Failed to create/get bot channel")
                await ctx.send("❌ Failed to create or access bot channel")
                return
            print(f"Bot channel setup successful: {bot_channel.name} ({bot_channel.id})")
        except Exception as e:
            await ctx.send(f"❌ Error during bot channel setup: {str(e)}")
            print(f"Bot channel error: {str(e)}")
            return
        
        # If we're not in the bot channel, redirect there
        if ctx.channel.id != bot_channel.id:
            await ctx.send(f"📢 Please use {bot_channel.mention} for bot commands!")
            print("Redirecting user to bot channel")
            return
        
        await ctx.send("🤔 Analyzing your server requirements...")
        print("Starting server analysis")
        
        example_json = '{"server_config": {"name": "Gaming Hub","verification_level": 1},"categories": [],"roles": []}'
        schema_json = '''{
    "server_config": {
        "name": "string",
        "verification_level": "number (0-4)",
        "explicit_content_filter": "number (0-2)",
        "afk_timeout": "number (60, 300, 900, 1800, 3600)"
    },
    "categories": [
        {
            "name": "string (with emoji)",
            "position": "number",
            "permissions": {
                "role_name": {
                    "view_channel": "boolean",
                    "send_messages": "boolean"
                }
            },
            "channels": [
                {
                    "name": "string (with emoji)",
                    "type": "text/voice/forum",
                    "topic": "string",
                    "position": "number",
                    "slowmode_delay": "number",
                    "nsfw": "boolean",
                    "permissions": {}
                }
            ]
        }
    ],
    "roles": [
        {
            "name": "string (with emoji)",
            "color": "string (hex color)",
            "hoist": "boolean",
            "mentionable": "boolean",
            "permissions": {
                "administrator": "boolean",
                "manage_channels": "boolean",
                "manage_roles": "boolean",
                "manage_messages": "boolean",
                "view_channel": "boolean",
                "send_messages": "boolean",
                "read_message_history": "boolean",
                "connect": "boolean",
                "speak": "boolean",
                "use_external_emojis": "boolean",
                "add_reactions": "boolean",
                "attach_files": "boolean",
                "embed_links": "boolean"
            }
        }
    ]
}'''
        
        prompt = f"""You are a Discord server structure generator. Based on this description: "{description}", create a Discord server structure.

IMPORTANT: You must ONLY return a valid JSON object. Do not include ANY explanatory text, markdown formatting, or code blocks.

Example of CORRECT response format:
{example_json}

The JSON structure must follow this schema:
{schema_json}

Rules:
1. ONLY return the JSON object, nothing else
2. Use emojis in names (📢, 💬, 🎮, 👑, etc.)
3. Channel names must be lowercase with hyphens
4. Maximum: 8 categories, 6 channels per category, 10 roles
5. All JSON must be valid with proper quotes and commas
6. All hex colors must be valid (e.g., "#FF0000")
7. All boolean values must be true or false, not strings
8. All number values must be actual numbers, not strings
9. Position values must start from 0 and be sequential
10. Do not add any fields not specified in the schema"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '', 1)
        if response_text.startswith('```'):
            response_text = response_text.replace('```', '', 1)
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            server_plan = json.loads(response_text)
            
            # Validate essential structure
            required_keys = ['server_config', 'categories', 'roles']
            if not all(key in server_plan for key in required_keys):
                await bot_channel.send("❌ Invalid server structure: Missing required sections. Please try again.")
                return
                
            # Basic validation of values
            if not isinstance(server_plan['categories'], list) or not isinstance(server_plan['roles'], list):
                await bot_channel.send("❌ Invalid server structure: Categories and roles must be lists. Please try again.")
                return
                
            if len(server_plan['categories']) > 8:
                await bot_channel.send("❌ Too many categories (maximum 8). Please try again.")
                return
                
            if len(server_plan['roles']) > 10:
                await bot_channel.send("❌ Too many roles (maximum 10). Please try again.")
                return
                
            for category in server_plan['categories']:
                if len(category.get('channels', [])) > 6:
                    await bot_channel.send("❌ Too many channels in a category (maximum 6). Please try again.")
                    return
            
            # Store the plan and show confirmation message
            bot.server_plans = getattr(bot, 'server_plans', {})
            bot.server_plans[ctx.guild.id] = server_plan
            
            # Show the planned structure
            plan_msg = "Here's the planned server structure:\n\n"
            plan_msg += f"**Server Configuration**\n"
            plan_msg += f"Name: {server_plan['server_config']['name']}\n\n"
            
            plan_msg += "**Categories and Channels**\n"
            for category in server_plan['categories']:
                plan_msg += f"📁 {category['name']}\n"
                for channel in category.get('channels', []):
                    channel_type = "💬" if channel['type'] == 'text' else "🔊" if channel['type'] == 'voice' else "📋"
                    plan_msg += f"  {channel_type} {channel['name']}\n"
            
            plan_msg += "\n**Roles**\n"
            for role in server_plan['roles']:
                plan_msg += f"👥 {role['name']}\n"
            
            plan_msg += "\nReview this structure and type `!confirm` to proceed with creation, or `!cancel` to start over."
            
            # Split message if it's too long
            if len(plan_msg) > 2000:
                parts = [plan_msg[i:i+1900] for i in range(0, len(plan_msg), 1900)]
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        await bot_channel.send(part)
                    else:
                        await bot_channel.send(part + "\n[continued in next message]")
            else:
                await bot_channel.send(plan_msg)
            
            # Interactive changes loop
            while True:
                await bot_channel.send("✨ Server structure has been created! Would you like to make any additional changes? (yes/no)")
                
                def check(m):
                    return m.author == ctx.author and m.channel == bot_channel and m.content.lower() in ['yes', 'no']
                
                try:
                    msg = await bot.wait_for('message', check=check, timeout=60.0)
                    if msg.content.lower() == 'no':
                        break
                    else:
                        await bot_channel.send("What additional changes would you like to make? Please describe them:")
                        try:
                            changes_msg = await bot.wait_for('message', timeout=60.0, 
                                check=lambda m: m.author == ctx.author and m.channel == bot_channel)
                            # Process additional changes here
                            await bot_channel.send("Processing your changes...")
                            # [Add your additional changes processing logic]
                        except asyncio.TimeoutError:
                            await bot_channel.send("⚠️ No response received. Moving on...")
                            break
                except asyncio.TimeoutError:
                    await bot_channel.send("⚠️ No response received. Moving on...")
                    break
            
            # Ask about cleanup
            await bot_channel.send("🧹 Would you like me to clean up the bot's channel and role? (yes/no)")
            try:
                cleanup_msg = await bot.wait_for('message', timeout=30.0, 
                    check=lambda m: m.author == ctx.author and m.channel == bot_channel and m.content.lower() in ['yes', 'no'])
                if cleanup_msg.content.lower() == 'yes':
                    await cleanup_bot_resources(ctx)
                    await ctx.send("✅ Bot resources have been cleaned up. Enjoy your new server!")
                else:
                    await bot_channel.send("✅ Bot resources will be preserved. Enjoy your new server!")
            except asyncio.TimeoutError:
                await bot_channel.send("⏳ No response received. Bot resources will be preserved.")
            
        except json.JSONDecodeError as e:
            await bot_channel.send(f"❌ Error parsing server structure: Invalid JSON format. Please try again.")
            return
        except Exception as e:
            await bot_channel.send(f"❌ Error validating server structure: {str(e)}. Please try again.")
            return
            
    except Exception as e:
        if bot_channel:
            await bot_channel.send(f"❌ An error occurred: {str(e)}")
        else:
            await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name='confirm')
@commands.has_permissions(administrator=True)
async def confirm_build(ctx):
    """Confirm and execute the server build plan"""
    try:
        server_plan = bot.server_plans.get(ctx.guild.id)
        if not server_plan:
            await ctx.send("No pending server build plan found. Use !build_server first!")
            return
            
        await create_server_structure(ctx, server_plan)
        # Clear the stored plan
        del bot.server_plans[ctx.guild.id]
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='cancel')
@commands.has_permissions(administrator=True)
async def cancel_build(ctx):
    """Cancel the pending server build"""
    try:
        if ctx.guild.id in getattr(bot, 'server_plans', {}):
            del bot.server_plans[ctx.guild.id]
            await ctx.send("❌ Server build cancelled!")
        else:
            await ctx.send("No pending server build to cancel!")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='ask')
async def ask_gemini(ctx, *, question):
    """Ask Gemini AI a question"""
    try:
        response = model.generate_content(question)
        await ctx.send(response.text)
    except Exception as e:
        await ctx.send(f"Sorry, I encountered an error: {str(e)}")

@bot.command(name='help_server')
async def help_server(ctx):
    """Display help information about server management commands"""
    help_text = """
**Server Management Commands:**
`!build_server <description>` - Design and build a server based on your description
`!confirm` - Confirm and execute the pending server build plan
`!cancel` - Cancel the pending server build plan
`!ask <question>` - Ask Gemini AI a question
`!help_server` - Show this help message

**Examples:**
1. Gaming Server:
`!build_server Create a gaming community server focused on Minecraft and other games, with separate areas for different games, voice channels for gaming sessions, role-based access, and community features`

2. Community Server:
`!build_server Create a vibrant community server with announcement channels, general chat, topic-specific discussions, voice hangouts, and special roles for moderators and active members`

3. Education Server:
`!build_server Create an educational server for a programming course with areas for announcements, general discussion, separate topics for different programming languages, homework help, and project collaboration`

The bot will create a complete server structure with:
- Server settings
- Categories with emojis
- Text, voice, and forum channels
- Roles with permissions
- Channel-specific permissions

⚠️ **Note**: Using !confirm will delete all existing channels and roles before creating the new structure!
    """
    await ctx.send(help_text)

async def generate_channels(description):
    """Generate channel structure based on description using AI"""
    try:
        prompt = f"""Generate a Discord channel structure based on this description: {description}
        Return a JSON object with an array of channels. Each channel should have:
        - name: channel name (use emojis where appropriate)
        - type: 'text', 'voice', or 'forum'
        - topic: channel topic/description
        - category: which category it belongs to
        Example format:
        {{
            "channels": [
                {{
                    "name": "🎮-gaming",
                    "type": "text",
                    "topic": "General gaming discussion",
                    "category": "Gaming"
                }}
            ]
        }}"""
        
        response = await generate_ai_response(prompt)
        return json.loads(response)
    except Exception as e:
        return {
            'channels': [
                {'name': 'new-channel', 'type': 'text', 'topic': 'New channel', 'category': 'General'}
            ]
        }

async def generate_roles(description):
    """Generate role structure based on description using AI"""
    try:
        prompt = f"""Generate Discord roles based on this description: {description}
        Return a JSON object with an array of roles. Each role should have:
        - name: role name
        - color: hex color code
        - hoist: boolean (should role be displayed separately)
        - mentionable: boolean
        - permissions: object of permission names and boolean values
        Example format:
        {{
            "roles": [
                {{
                    "name": "Admin",
                    "color": "#FF0000",
                    "hoist": true,
                    "mentionable": true,
                    "permissions": {{"administrator": true}}
                }}
            ]
        }}"""
        
        response = await generate_ai_response(prompt)
        return json.loads(response)
    except Exception as e:
        return {
            'roles': [
                {'name': 'new-role', 'color': '#99AAB5', 'hoist': True, 'mentionable': True, 'permissions': {}}
            ]
        }

async def generate_channel_content(channel_name, description):
    """Generate formatted content for a channel using AI"""
    try:
        prompt = f"""Generate formatted Discord channel content for a channel named '{channel_name}' based on this description: {description}
        
        If it's a rules channel, include:
        - Server rules with explanations
        - Consequences for breaking rules
        - How to report violations
        
        If it's an info/welcome channel, include:
        - Warm welcome message
        - Server description
        - How to get roles
        - Channel navigation guide
        
        If it's an announcement channel, include:
        - Announcement template
        - Types of announcements to expect
        
        Use Discord markdown formatting:
        - **bold** for headers
        - *italic* for emphasis
        - > for quotes
        - • for bullet points
        - Emojis where appropriate
        
        Make it engaging and community-friendly!"""
        
        response = await generate_ai_response(prompt)
        return response
    except Exception as e:
        if 'rules' in channel_name.lower():
            return """**Server Rules**\n\n1. Be respectful\n2. No spam\n3. Follow Discord TOS"""
        elif 'info' in channel_name.lower():
            return """**Welcome to our server!**\n\nThis is an awesome community for gaming and fun!"""
        else:
            return description

async def process_additional_changes(ctx, change_type, description):
    """Process additional changes based on type and description"""
    try:
        if change_type == "channels":
            new_structure = await generate_channels(description)
            await ctx.send("🔨 Creating new channels...")
            for channel in new_structure['channels']:
                try:
                    category = None
                    # Try to find or create category
                    for existing_category in ctx.guild.categories:
                        if existing_category.name.lower() == channel['category'].lower():
                            category = existing_category
                            break
                    if not category:
                        category = await ctx.guild.create_category(channel['category'])
                        await ctx.send(f"✅ Created category: {category.name}")
                    
                    if channel['type'] == 'text':
                        await category.create_text_channel(
                            name=channel['name'],
                            topic=channel['topic']
                        )
                    elif channel['type'] == 'voice':
                        await category.create_voice_channel(name=channel['name'])
                    elif channel['type'] == 'forum':
                        await category.create_forum(
                            name=channel['name'],
                            topic=channel['topic']
                        )
                    await ctx.send(f"✅ Created {channel['type']} channel: {channel['name']}")
                except Exception as e:
                    await ctx.send(f"⚠️ Error creating channel {channel['name']}: {str(e)}")
                    
        elif change_type == "roles":
            new_structure = await generate_roles(description)
            await ctx.send("🔨 Creating new roles...")
            for role in new_structure['roles']:
                try:
                    await ctx.guild.create_role(
                        name=role['name'],
                        color=discord.Color.from_str(role['color']),
                        hoist=role['hoist'],
                        mentionable=role['mentionable'],
                        permissions=discord.Permissions(**role['permissions'])
                    )
                    await ctx.send(f"✅ Created role: {role['name']}")
                except Exception as e:
                    await ctx.send(f"⚠️ Error creating role {role['name']}: {str(e)}")
                    
        elif change_type == "content":
            channels = [c for c in ctx.guild.channels if isinstance(c, discord.TextChannel)]
            channel_list = "\n".join([f"{i+1}. {c.name}" for i, c in enumerate(channels)])
            await ctx.send(f"Which channel would you like to add content to? (enter the number)\n{channel_list}")
            
            try:
                msg = await bot.wait_for('message', timeout=30.0, 
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(channels))
                
                selected_channel = channels[int(msg.content)-1]
                content = await generate_channel_content(selected_channel.name, description)
                await selected_channel.send(content)
                await ctx.send(f"✅ Added content to #{selected_channel.name}")
            except asyncio.TimeoutError:
                await ctx.send("No response received, skipping content addition")
                
    except Exception as e:
        await ctx.send(f"❌ Error processing changes: {str(e)}")

@bot.command(name='add')
@commands.has_permissions(administrator=True)
async def add_server_content(ctx, content_type: str, *, description: str):
    """Add more content to the server
    Usage: 
    !add channels <description of channels to add>
    !add roles <description of roles to add>
    !add content <description of content to add>"""
    
    content_type = content_type.lower()
    if content_type not in ['channels', 'roles', 'content']:
        await ctx.send("Invalid content type. Use: channels, roles, or content")
        return
        
    await ctx.send(f"🔨 Processing your request to add {content_type}...")
    await process_additional_changes(ctx, content_type, description)

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
