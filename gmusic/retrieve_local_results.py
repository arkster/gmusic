# -*- coding: utf-8 -*-

"""
gmusic.retrieve_local_results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides helper functions to query and update a Pandas DataFrame

"""

import pandas as pd
import datetime
from gmusic.fetch_songs import FetchSongs


class QueryUsingPandas(object):
    """
    This module provides some helper functions for accessing title, artist info from a Pandas DF
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        if hasattr(self, 'google_music_json_file'):
            if not self.google_music_json_file:
                self.google_music_json_file = '/home/ark/work/Misc/google_music_content_new.json'

        if hasattr(self, 'name'):
            if not self.name:
                self.name = ''.join(['Alt-Radio-Station-', datetime.datetime.now().strftime('%m%d%Y%H%M%S%f')])

    def load_and_save_pandas_dataframe(self, load_or_save=None, dataframe=None):
        if load_or_save == 'load':
            return pd.read_json(self.google_music_json_file)
        elif load_or_save == 'save':
            dataframe.to_json(self.google_music_json_file)

    @classmethod
    def check_song_in_pandas_dataframe(self, dataframe, artist, song):
        if ((dataframe.artist.str.contains(artist, case=False)) & (
                dataframe.title.str.contains(song, case=False))).any():
            return True
        else:
            return False

    @classmethod
    def playlists_with_available_space(self, dataframe):
        """This method will calculate the playlist available space for songs"""

        unique_playlists = dataframe.playlist_id.unique()
        for playlist in unique_playlists:
            playlist_song_count = dataframe.playlist_id.value_counts()[playlist]
            if playlist_song_count < 800:
                yield(playlist, playlist_song_count)
            else:
                return None

    @classmethod
    def get_playlist(self, dataframe=None, remaining_songs=None, new_music_list=None, playlist=None, name=None):
        """

        :param dataframe: pandas dataframe
        :param remaining_songs: To be used only by the recursive call
        :param new_music_list: List of songs as input to calculate the space required in the playlists
        :param playlist: To be used exclusively by the recursive call (similar to the remaining_songs param above)
        :return:
        """
        song_set = remaining_songs if remaining_songs else len(new_music_list)

        if playlist:

            if remaining_songs > 800:
                yield (playlist, 800)
                remaining_songs = remaining_songs - 800
                yield from self.get_playlist(remaining_songs=remaining_songs, playlist=FetchSongs.create_gmusic_playlist(self.name))
            else:

                yield (playlist, remaining_songs)

        else:
            for each_returned_list in self.playlists_with_available_space(dataframe):

                if each_returned_list:
                    available_slots = 800 - each_returned_list[1]

                if available_slots:

                    if song_set >= available_slots:
                        remaining_songs = song_set - available_slots
                    else:
                        available_slots = song_set
                        remaining_songs = 0

                    yield (each_returned_list[0], available_slots)

                if remaining_songs:
                    song_set = remaining_songs
                else:
                    break
            else:
                if remaining_songs:
                    yield from self.get_playlist(remaining_songs=remaining_songs, playlist=FetchSongs.create_gmusic_playlist(self.name))

    @classmethod
    def append_to_pandas_dataframe(self, dataframe, song_list):
        return dataframe.append(pd.DataFrame(song_list, columns=['artist', 'title', 'nid', 'timestamp', 'playlist_id']), ignore_index=True)
