import discord
import requests
import random
from PIL import Image, ImageFilter
from io import BytesIO
from dotenv import load_dotenv
import os
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
# Stocke les parties en cours par salon { channel_id: pokemon_name }
active_games = {}
def fetch_pokemon():
    pokemon_id = random.randint(1, 151)
    r = requests.get(f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}')
    if r.status_code != 200:
        return None, None
    french_names = [e for e in r.json()['names'] if e['language']['name'] == 'fr']
    if not french_names:
        return None, None
    name = french_names[0]['name'].lower()
    r2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}')
    if r2.status_code != 200:
        return name, None
    sprite_url = r2.json()['sprites']['other']['official-artwork']['front_default']
    img_data = requests.get(sprite_url).content
    image = Image.open(BytesIO(img_data)).resize((300, 300))
    return name, image
def make_blurred_file(image):
    """Retourne un discord.File de l'image floutée."""
    blurred = image.filter(ImageFilter.GaussianBlur(radius=15))
    buf = BytesIO()
    blurred.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="pokemon.png")
@client.event
async def on_ready():
    print(f'Bot connecté : {client.user}')
@client.event
async def on_message(message):
    if message.author.bot:
        return
    channel_id = message.channel.id
    # Commande !pokemon : lance une partie
    if message.content.lower() == "!pokemon":
        if channel_id in active_games:
            await message.channel.send("Une partie est déjà en cours ! Devinez le Pokémon.")
            return
        await message.channel.send("Chargement du Pokémon... ⏳")
        name, image = fetch_pokemon()
        if not name or not image:
            await message.channel.send("Erreur lors du chargement, réessayez.")
            return
        active_games[channel_id] = name
        file = make_blurred_file(image)
        await message.channel.send("**Who's that Pokémon ?!** 🎮", file=file)
        return
    if message.content.lower() == "!abandon":
        if channel_id not in active_games:
            await message.channel.send("Aucune partie en cours. Tapez `!pokemon` pour jouer !")
            return
        name = active_games.pop(channel_id)
        await message.channel.send(f"😔 C'était **{name.capitalize()}** ! Tapez `!pokemon` pour rejouer.")
        return
    # Tentative de réponse si une partie est en cours
    if channel_id in active_games:
        guess = message.content.strip().lower()
        name = active_games[channel_id]
        if guess == name:
            active_games.pop(channel_id)
            await message.channel.send(
                f"🎉 Bravo {message.author.mention} ! C'était bien **{name.capitalize()}** !\n"
                f"Tapez `!pokemon` pour rejouer."
            )
client.run(TOKEN)