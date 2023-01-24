from playlists import Playlist
from discord import Embed
from discord.ext.commands import Context


async def send_playlist_message(playlist: Playlist, ctx: Context):
    embed = Embed(title=f"Playlist: {playlist.name}", color=0x00ff00)
    for title, _ in playlist.songs.items():
        embed.add_field(name=title, value=None, inline=False)

    message = await ctx.channel.send(embed=embed)
    await message.add_reaction('⏯')  # play
    await message.add_reaction('⏹')  # stop
    await message.add_reaction('⏮')  # previous
    await message.add_reaction('⏭')  # next
    await message.add_reaction('🔀')  # shuffle

    return message
