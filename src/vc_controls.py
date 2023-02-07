from typing import Callable, Any

from discord import VoiceClient, VoiceChannel, FFmpegPCMAudio
from utils import configure_logger
import logging
import functools


def safe_exec(func):
    @functools.wraps(func)
    def wrapper(vc_controls, *args, **kwargs):
        if vc_controls.voice_client is None:
            vc_controls.logger.warning("The voice client is uninitialized")
            return

        return func(vc_controls, *args, **kwargs)

    return wrapper


class VoiceClientControl:
    def __init__(self):
        self.voice_client = None
        self.logger: logging.Logger = configure_logger("VoiceClientControl")
        self._playing = False

    async def connect(self, voice_channel: VoiceChannel):
        if voice_channel is None:
            raise ValueError("The provided voice channel is uninitialized")

        self.voice_client: VoiceClient = await voice_channel.connect()

    @safe_exec
    async def disconnect(self):
        if self.voice_client.is_connected():
            await self.voice_client.disconnect(force=True)

    @property
    @safe_exec
    def playing(self):
        return self.voice_client.is_playing()

    @safe_exec
    def play(self, source):
        self.stop()
        self.logger.info(f"Playing sound: {source}")
        self.voice_client.play(FFmpegPCMAudio(source))

    @safe_exec
    def stop(self):
        if self.playing:
            self.logger.info("Stopping voice client")
            self.voice_client.stop()

    @safe_exec
    def toggle_play(self):
        if self.playing:
            self.logger.info("Pausing voice client")
            self.voice_client.pause()
        else:
            self.logger.info("Resuming voice client")
            self.voice_client.resume()
