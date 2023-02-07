import asyncio
import os.path
from typing import Any, Coroutine, Optional

from discord import FFmpegPCMAudio, Game, Message, Reaction, VoiceClient, VoiceChannel, Intents
from discord.ext.commands import Bot
from flask import Flask, Response, render_template, request, redirect, url_for

from messages import *
from playlists import *
from utils import *
from threading import Thread

from vc_controls import VoiceClientControl


class MondiBot(Bot):
    def __init__(self, sounds_dir: str = "../sounds", command_prefix="*", intents=Intents.all()):

        super().__init__(command_prefix=command_prefix, intents=intents)

        self.pl_finder = PlaylistFinder()
        self.playlist_control_task: Optional[asyncio.Task] = None
        self.playlist: Playlist = None
        self.vc_controls = VoiceClientControl()

        self.command_prefix: str = command_prefix
        self.sounds_dir = sounds_dir

        self.logger: logging.Logger = configure_logger("MondiBot")

        self.api = Flask("MondiBot")
        self.api.template_folder = os.path.join(os.path.dirname(__file__), "templates")
        self.api_thread: Thread = None
        self.api.add_url_rule("/trigger/<audio_file>", "play", self.play, methods=["GET"])
        self.api.add_url_rule("/sounds/", "sounds", self.sounds, methods=["GET"])

        self.ctx: Context = None

        self.command_mapping = {
            f"{self.command_prefix}join": self.join,
            f"{self.command_prefix}leave": self.leave,
            f"{self.command_prefix}alma": self.alma,
            f"{self.command_prefix}playlist": self.get_playlist
        }

    async def on_ready(self):
        self.logger.info("Logged on as {self.user}!")
        self.api_thread = Thread(target=self.api.run, args=(
            os.getenv("FS_HOST"),
            os.getenv("FS_PORT"))
        )

        self.api_thread.daemon = True
        self.api_thread.start()
        await self.change_presence(activity=Game(name="with Alma's bean"))

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        user: str = str(message.author).split("#")[0]
        user_message: str = str(message.content)
        channel: str = str(message.channel.name)
        self.logger.info(f'Message from {user}: {user_message} in {channel}')

        cmd: str = user_message.lower().split(" ")[0]
        if cmd in self.command_mapping:
            await self.command_mapping[cmd](message)

    async def join(self, ctx: Context):
        if ctx.author.voice:
            self.ctx = ctx
            await self.vc_controls.connect(ctx.author.voice.channel)
        else:
            self.logger.warning("You are not connected to a voice channel")

    async def leave(self, ctx: Context):
        if ctx.author.voice:
            await self.vc_controls.disconnect()
            self.ctx = None
        else:
            self.logger.warning("The bot is not connected to a voice channel")

    async def get_playlist(self, ctx: Message) -> Coroutine[Any, Any, None] | None:
        channel = ctx.channel
        playlist_id = ctx.content.split(" ")[1]

        if len(playlist_id) < 2:
            self.logger.warning("No playlist id provided")
            await channel.send("No playlist id provided")
            return

        await self.start_playlist_in_channel(channel, playlist_id)

    async def start_playlist_in_channel(self, channel, playlist_id) -> None:
        message: Message = await channel.send("Searching for the songs in the spotify playlist "
                                              "on youtube. This might take a while...")

        playlist_name, songs = self.pl_finder.find_sp_playlist(os.getenv("SPOTIPY_USER_ID"), playlist_id)
        youtube_songs = self.pl_finder.find_yt_songs(songs)
        self.playlist = Playlist(playlist_name, youtube_songs)
        self.playlist_control_task = asyncio.create_task(self.control_playlist())
        await message.delete()

    async def control_playlist(self):
        if self.playlist is None:
            self.logger.warning("No playlist has been loaded")
            await self.ctx.channel.send("No playlist has been loaded. Please use"
                                        "the download command to load a playlist")
            return

        message = await send_playlist_message(self.playlist, self.ctx)

        def check(user_reaction: Reaction, user):
            selected_emoji: str = str(user_reaction.emoji)
            return user == self.ctx.author and str(selected_emoji) in ['⏯', '⏹', '⏮', '⏭', '🔀'] \
                   and user_reaction.message.id == message.id

        while True:
            try:
                reaction, _ = await self.wait_for('reaction_add', check=check)
                emoji = str(reaction.emoji)
                if emoji == '🔀':
                    self.vc_controls.play(self.playlist.pick_random_song())
                elif emoji == '⏮':
                    self.vc_controls.play(self.playlist.prev_song())
                elif emoji == '⏭':
                    self.vc_controls.play(self.playlist.next_song())
                elif emoji == '⏯':
                    self.vc_controls.toggle_play()
                elif emoji == '⏹':
                    self.vc_controls.stop()
                    await message.delete()
                    self.playlist = None
                    self.playlist_control_task.cancel()
                    return
            except asyncio.CancelledError:
                self.logger.error("The playlist control task has been cancelled", exc_info=True)
                break
            except Exception:
                self.logger.error("An error occurred while controlling the playlist", exc_info=True)

            await asyncio.sleep(1)

    async def alma(self, ctx: Context):
        users = list(ctx.guild.members)
        user = random.choice(users)
        channel = ctx.channel
        await channel.send(f"Almen e ngopi: {user.mention}")

    def play(self, audio_file: str):
        source = os.path.join(self.sounds_dir, audio_file) + ".mp3"
        self.vc_controls.play(source)

        return redirect("/sounds")

    def sounds(self):
        if not os.path.exists(self.sounds_dir):
            return Response("The sounds directory does not exist", status=500)

        sounds = [file_name[:-4] for file_name in os.listdir(self.sounds_dir) if file_name.endswith(".mp3")]
        return Response(render_template("sounds.html", mp3_files=sounds), status=200)
