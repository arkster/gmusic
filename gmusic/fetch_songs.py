# -*- coding: utf-8 -*-

"""
gmusic.fetch_songs
~~~~~~~~~~~~~~~~~~~~~

This module runs the main process to fetch the play gmusic songs
"""

from gmusicapi import Mobileclient
import os
import box


class FetchSongs(object):
    """
        Class to manage updating and creating of playlists and songs in the Google Play Music service for a specific
         Play Music account
    """

    def __init__(self):

        self.songs = []
        self.nids = []

        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'

        self.api = Mobileclient()
        self.api.login('xxxxxx', 'xxxxx', Mobileclient.FROM_MAC_ADDRESS)

    def add_songs_to_gmusic_playlist(self, playlist_id, song_ids):
        """ Add songs to the GMUSIC API playlist using song ids

        :param playlist_id: str playlist id
        :param song_ids: list of strings
        :returns: None
        """

        return self.api.add_songs_to_playlist(playlist_id, song_ids)

    def search_for_songs(self, artist, title):
        """ Search for songs in the GMUSIC API

        :param artist: string
        :param title: string
        :return song_nid: string
        """

        song_nid = None
        search_content = self.api.search(''.join([artist, ' ', title]))
        for each_song in search_content['song_hits']:
            song_detail = box.Box(each_song['track'])
            if artist.casefold() in song_detail.artist.casefold() and title.casefold() in song_detail.title.casefold():
                song_nid = song_detail.storeId
                break
        return song_nid

    def get_playlists_length(self, api_content):
        """ Get size of GMUSIC playlists in terms of number of songs

        :param api_content: dict
        :returns playlist_sizes: dict
        """

        playlist_sizes = {}
        api_playlists = self.api.get_all_playlists()
        for api_playlist in api_playlists:
            for content_playlist in api_content:
                if content_playlist['id'] == api_playlist['id']:
                    playlist_sizes[api_playlist['id']] = len(content_playlist['tracks'])
        return playlist_sizes

    def get_available_playlists(playlist_dict):
        """ Get available playlist ids and associated number of songs
        :param playlist_dict: dict
        :return list_id, number_of_songs: tuple of list_id and number of songs
        """

        available_lists = {k for (k, v) in playlist_dict.items() if v <= 800}
        if available_lists:
            for list_id, number_of_songs in available_lists.items():
                yield (list_id, number_of_songs)
        else:
            return None

    @classmethod
    def create_gmusic_playlist(self, name):
        """ Create GMUSIC playlist
        :param name: string name of playlist
        :return: string success or fail"""
        return self.api.create_playlist(name)
