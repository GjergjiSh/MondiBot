import random
from dataclasses import dataclass
from typing import Dict

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_dl import YoutubeDL

from utils import *


@dataclass
class Song:
    def __init__(self, title, source, spotify_title=None):
        self.title = title
        self.source = source
        self.spotify_title = spotify_title


@dataclass
class Playlist:
    def __init__(self, name: str, songs: list[Song]):
        self.name = name
        self.current_song = 0
        self.logger = configure_logger("Playlist")
        self.songs: dict[str, str] = {}
        for song in songs:
            self.songs[song.title] = song.source

    def pick_random_song(self) -> str:
        song_title = random.choice(list(self.songs.keys()))
        song_source = self.songs[song_title]
        self.current_song = list(self.songs.keys()).index(song_title)
        self.logger.info(f"Playlist {self.name} - song index: {self.current_song} title: {song_title}")
        return song_source

    def next_song(self) -> str:
        song_titles = list(self.songs.keys())
        self.current_song = (self.current_song + 1) % len(song_titles)
        song_title = song_titles[self.current_song]
        self.logger.info(f"Playlist {self.name} - song index: {self.current_song} title: {song_title}")
        return self.songs[song_title]

    def prev_song(self) -> str:
        song_titles = list(self.songs.keys())
        self.current_song = (self.current_song - 1) % len(song_titles)
        song_title = song_titles[self.current_song]
        self.logger.info(f"Playlist {self.name} - song index: {self.current_song} title: {song_title}")
        return self.songs[song_title]


class PlaylistFinder:
    def __init__(self) -> None:
        self.vdl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        self.logger = configure_logger("PlaylistFinder")

    def find_sp_playlist(self, username, playlist_id) -> tuple[str, str]:
        results = self.sp.user_playlist(username, playlist_id)
        songs = results["tracks"]["items"]
        playlist_name = results["name"]

        # TODO Artist
        # for song in songs:
        #     self.logger.info(song["track"]["name"])

        return playlist_name, songs

    def find_yt_songs(self, spotify_songs) -> list[Song]:
        youtube_songs: list[Song] = []
        for song in spotify_songs:
            spotify_song_title: str = song["track"]["name"]

            with YoutubeDL(self.vdl_options) as ydl:
                try:
                    info: Dict = ydl.extract_info("ytsearch:%s" % spotify_song_title, download=False)['entries'][0]
                    song_source: str = info['formats'][0]['url']
                    song_title: str = info['title']
                    self.logger.info(f"Found {song_title} in youtube for spotify song {spotify_song_title}.")
                    youtube_songs.append(Song(song_title, song_source, spotify_song_title))
                except Exception:
                    self.logger.error(f"Error when searching for {spotify_song_title} in youtube.", exc_info=True)

        return youtube_songs
