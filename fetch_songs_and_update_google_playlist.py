# -*- coding: utf-8 -*-

"""
gmusic.fetch_songs_and_update_google_playlist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Main function to initialize and fetch, query, update local and on google playlists


"""

from gmusic.media_resources import MediaResources
from gmusic.fetch_songs import FetchSongs
from gmusic.retrieve_local_results import QueryUsingPandas
import box
import asyncio
from halo import Halo
import datetime


def main():
    """Main function to provide the logic to setup the gmusicapi connection, query radio stations for song information,
    check the local database if the songs exist and if not, query google gmusic for the song ids and then update a google gmusic
    playlist with them. Subsequently update the local database with the addded song to the playlist.

    Playlists are managed by the number of songs that they can contain. If a playlist has over 900 songs, we query to see if any
    other playlists exist that contain < 900 songs and add the songs to them.

    """

    # first query for gmusic from websites
    media_resources = MediaResources(steps=3)

    # use box so that we can retrieve dictionary fields in a more elegant manner
    box_radio_stations = box.Box(media_resources.radio_stations)

    spinner = Halo(text='Running asynchronous fetch on websites', spinner='dots')
    spinner.start()
    spinner.color = 'magenta'

    # process async stations first
    # get the loop for the cbs stations
    loop = asyncio.get_event_loop()

    # loop over the cbs stations first
    for radio_station, url in box_radio_stations.cbs_stations.urls.items():
        # pull parameters from media_resources.radio_stations
        cbs_params = box_radio_stations.cbs_stations.params
        box_radio_stations.cbs_stations.headers.Referer = url
        interval = box_radio_stations.cbs_stations.interval

        playlist_songs_from_cbs_stations = loop.run_until_complete(
            media_resources.run_loop(loop, headers=box_radio_stations.cbs_stations.headers, url=url, params=cbs_params,
                                     station='cbs_stations', interval=interval))

        media_resources.parse_cbs_station_data(playlist_songs_from_cbs_stations)
    loop.close()
    #
    # # process tunegenie stations next
    # # get the loop
    loop_again = asyncio.new_event_loop()

    for radio_station, url in box_radio_stations.tunegenie.urls.items():
        # parameters are similar to above
        tunegenie_params = box_radio_stations.tunegenie.params
        box_radio_stations.tunegenie.headers.Referer = url
        interval = box_radio_stations.tunegenie.interval

        playlist_songs_from_tunegenie_stations = loop_again.run_until_complete(
            media_resources.run_loop(loop_again, headers=box_radio_stations.tunegenie.headers, url=url,
                                     params=tunegenie_params, station='tunegenie', interval=interval))

        media_resources.parse_tunegenie_data(playlist_songs_from_tunegenie_stations)
    loop_again.close()

    spinner.succeed()
    spinner.color = 'cyan'
    spinner.text = "Running synchronous fetch on websites"

    # run synchronous get for the other stations
    spinner.start()
    media_resources.run_synchronous_process()
    spinner.succeed()

    # create google api search setup
    google_music_fetch = FetchSongs()

    # remove duplicates
    # first convert to set
    media_set = set(tuple(item) for item in media_resources.music_list)
    music_list = [list(item) for item in media_set]

    if not music_list:
        # log
        spinner.text = "Unable to retrieve song data from websites"
        spinner.fail()
        exit()

    # load pandas dataframe
    pandas_init = QueryUsingPandas(load_or_save=None, google_music_json_file=None, dataframe=None, remaining_songs=None,
                                   new_music_list=None, playlist=None, name=None, song_list=None)
    music_dataframe = pandas_init.load_and_save_pandas_dataframe(load_or_save='load')

    # create a filter to remove words that contain the following
    myfilter = ['**', '[', ']', '(', ')', '+']
    song_list = []
    # check if each song in music_list is in the pandas df
    for index, each_song in enumerate(music_list):
        artist, song = each_song[0], each_song[1]
        song = ' '.join([title for title in song.split(" ") if not any(i in title for i in myfilter)])
        artist = ' '.join([singer for singer in artist.split(" ") if not any(i in singer for i in myfilter)])

        if '??' in song or '??' in artist:
            continue

        if pandas_init.check_song_in_pandas_dataframe(dataframe=music_dataframe, artist=artist, song=song):
            # music_list.pop(index)
            continue

        # need to save the timestamp as well
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # search for song in google play
        # print("Searching for nid for song", song, "by", artist)
        song_nid = google_music_fetch.search_for_songs(artist=artist, title=song)
        # print("Found nid", song_nid)

        if song_nid:
            song_list.append([artist, song, song_nid, timestamp])
        else:
            # song not found in google play
            continue

    # now that we have the song_list, we can now query for a playlist to so that we can append it
    # create dictionaries for each playlist_id where the value for the playlist key will be a list of lists
    start_index = 0
    for playlist_info in pandas_init.get_playlist(dataframe=music_dataframe, new_music_list=song_list):
        song_ids = []
        if playlist_info and len(playlist_info) == 2:
            playlist_id, playlist_slots = playlist_info[0], playlist_info[1]

        else:
            print("Need to log error")
        print(playlist_id, playlist_slots)
        # if not song_dict[playlist_id]:
        #     song_dict[playlist_id].append([])

        for each_song_list in song_list:
            each_song_list.append(playlist_id)

            song_ids.append(each_song_list[2])

        # now for the final phase. Update the playlist at Play Music with the songids
        if song_ids:
            print(google_music_fetch.add_songs_to_gmusic_playlist(playlist_id,
                                                                  song_ids[start_index:start_index + playlist_slots]))
            start_index = playlist_slots

    print(song_list)
    # update the pandas_dataframe
    music_dataframe = QueryUsingPandas.append_to_pandas_dataframe(dataframe=music_dataframe, song_list=song_list)
    pandas_init.load_and_save_pandas_dataframe(dataframe=music_dataframe, load_or_save='save')

    import pickle
    pickle.dump(song_list, open('/tmp/pickle1', 'wb'))


if __name__ == '__main__':
    main()
