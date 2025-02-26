import discord
from discord.ui import Button, View
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
import asyncio

class TwitchNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch = None
        self.streamers_status = {}
        
    async def initialize_twitch(self, client_id, client_secret, streamers):
        self.twitch = await Twitch(client_id, client_secret)
        self.streamers_status = {streamer.lower(): False for streamer in streamers}
        self.check_streams.start()

    @tasks.loop(seconds=1)  # Ahora revisará cada 10 segundos en vez de 1 minuto
    async def check_streams(self):
        if not self.twitch:
            return
            
        try:
            users = []
            async for user in self.twitch.get_users(logins=list(self.streamers_status.keys())):
                users.append(user)
            
            if not users:
                return
                
            user_map = {str(user.id): user.login for user in users}
            
            live_streams = {}
            async for stream in self.twitch.get_streams(user_id=list(user_map.keys())):
                live_streams[str(stream.user_id)] = stream
            
            channel = self.bot.get_channel(CHANNEL_ID)
            if not channel:
                print(f"No se pudo encontrar el canal con ID {CHANNEL_ID}")
                return
            
            for user_id, username in user_map.items():
                is_live = user_id in live_streams
                username_lower = username.lower()
                
                if is_live and not self.streamers_status[username_lower]:
                    stream_data = live_streams[user_id]
                    stream_title = stream_data.title
                    stream_game = stream_data.game_name or 'Just Chatting'
                    stream_viewers = stream_data.viewer_count
                    stream_url = f"https://www.twitch.tv/{username}"
                    stream_thumbnail = stream_data.thumbnail_url.replace("{width}", "1280").replace("{height}", "720")
                    
                    embed = discord.Embed(
                        title=f"{username} esta on en Twitch!",
                        description=f"[{stream_title}]({stream_url})",
                        color=0x6441a5
                    )
                    embed.add_field(name="Jugando", value=stream_game, inline=True)
                    embed.add_field(name="Viewers", value=str(stream_viewers), inline=True)
                    embed.set_image(url=stream_thumbnail)
                    embed.set_thumbnail(url="https://static.twitchcdn.net/assets/favicon-32-d6025c14e900565d6177.png")
                    
                    button = Button(label="Entrar al stream", url=stream_url, style=discord.ButtonStyle.link)
                    view = View()
                    view.add_item(button)
                    
                    await channel.send(content=f"@everyone ¡{username} ha iniciado stream!", embed=embed, view=view)
                    print(f"Notificación enviada para {username}")
                
                self.streamers_status[username_lower] = is_live
                
        except Exception as e:
            print(f"Error checking streams status: {e}")
            import traceback
            traceback.print_exc()

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()

# Configuración
TWITCH_CLIENT_ID = 'cplf97vljjq97hhjtwpqnru78f5up6'
TWITCH_CLIENT_SECRET = 'l4kf4uea2ghejo3t9tq50senp5hbth'
CHANNEL_ID = 1090826565270642698  # ID del canal de Discord
STREAMERS = ['pablitorelojero', 'selkie_', 'xtomiiii']
DISCORD_TOKEN = ''

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    notifier = TwitchNotifier(bot)
    await notifier.initialize_twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, STREAMERS)
    await bot.add_cog(notifier)

def main():
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
