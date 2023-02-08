import random
from dataclasses import dataclass

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_dl import YoutubeDL

from utils import *


@dataclass
class Song:
    name: str
    artists: list[str]
    webpage_url: str
    url: str

    def __init__(self, name: str, artists: list[str] = None,
                 webpage_url=None, url=None):
        self.name = name
        self.artists = artists
        self.webpage_url = webpage_url
        self.url = url


@dataclass
class Playlist:
    def __init__(self, name: str, songs: list[Song]):
        self.name = name
        self.songs = songs
        self.current_song = self.songs[0]
        self.logger = configure_logger("Playlist")

    def pick_random_song(self) -> Song:
        self.current_song = random.choice(self.songs)
        return self.current_song

    def next_song(self) -> Song:
        current_song_idx = self.songs.index(self.current_song)
        next_song_idx = (current_song_idx + 1) % len(self.songs)
        self.current_song = self.songs[next_song_idx]
        return self.current_song

    def prev_song(self) -> Song:
        current_song_idx = self.songs.index(self.current_song)
        prev_song_index = (current_song_idx - 1) % len(self.songs)
        self.current_song = self.songs[prev_song_index]
        return self.current_song


class PlaylistFinder:
    def __init__(self) -> None:
        self.vdl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        self.logger = configure_logger("PlaylistFinder")

    def get_playlist(self, playlist_id: str) -> Playlist:
        # Find the spotify playlist
        search_results = self.sp.playlist(playlist_id)
        playlist_name = search_results["name"]
        if not search_results:
            raise RuntimeWarning(f"Failed to find the playlist for {playlist_id}")

        # For each song in the spotify playlist
        songs = []
        for song in search_results["tracks"]["items"]:
            song_name = song["track"]["name"]
            song_artists = [artist["name"] for artist in song["track"]["artists"]]

            # Find a matching counterpart in YouTube
            with YoutubeDL() as vdl:
                # Add the artists to the search string
                search_artists = " ".join(song_artists)
                yt_matches = vdl.extract_info(
                    f"ytsearch:{song_name} {search_artists}",
                    download=False)

            if yt_matches:
                # Remove the entry if it's not a Music video
                matches = yt_matches['entries']
                for idx, match in enumerate(matches):
                    categories = match["categories"]
                    if "Music" not in categories:
                        matches.pop(idx)

                # Add the song to the list
                if matches:
                    name = matches[0]["title"]
                    webpage_url = matches[0]['webpage_url']
                    url = matches[0]['formats'][0]['url']
                    songs.append(Song(name, song_artists, webpage_url, url))

        return Playlist(playlist_name, songs)


if __name__ == "__main__":
    pl_finder = PlaylistFinder()
    playlist = pl_finder.get_playlist("1kOdZWDxeOIkQR20HIvLyf")
    for song in playlist.songs:
        print(song)

    print(playlist.pick_random_song())
    print(playlist.next_song())
    print(playlist.prev_song())
