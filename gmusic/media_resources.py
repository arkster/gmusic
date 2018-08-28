# -*- coding: utf-8 -*-

"""
gmusic.media_resources
~~~~~~~~~~~~~~~~~~~~~~

This module queries various radio stations to gather recently played songs on their playlists

"""

from datetime import datetime, timedelta
from random import randint
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import box


class MediaResources(object):
    """
    Main class that queries for songs
    """

    def __init__(self, timestamp=None, steps=None):
        if not steps:
            self.steps = 50000
        else:
            self.steps = steps

        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = None
        self.music_list = []

        self.radio_stations = {
            'cbs_stations': {
                'params':
                    [['action', 'playlist'], ['type', 'json'], ['before']]
                ,
                'headers': {
                    'DNT': '1',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
                    'Accept': '*/*',
                    'Referer': 'http://{}.cbslocal.com/playlist',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Connection': 'keep-alive',
                },
                'urls': {
                    'wxrt': 'http://wxrt.cbslocal.com/playlist/',
                    'x1075lasvegas': 'http://x1075.cbslocal.com/playlist',
                    'kroq': 'http://www.roq.com/playlist/',
                    'live105': 'http://www.live.com/playlist/',
                },
                'interval': self.steps * 4,
            },
            'tunegenie': {
                'params': [['since', '2017-08-08T17:00:00-05:00'], ['until', '2017-08-08T18:59:59-05:00']],
                'headers': {
                    'DNT': '1',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                    'Accept': '*/*',
                    'Referer': 'http://{}.tunegenie.com/onair/',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Connection': 'keep-alive',
                },
                'urls': {
                    'wwyy': 'http://wwyy.tunegenie.com/api/v1/brand/nowplaying/',
                    'wkqx': 'http://wkqx.tunegenie.com/api/v1/brand/nowplaying/'
                },
                'interval': self.steps * 4,
            },
            'iheart': {
                'stations': ['star1019', 'dc101'],
                # 'stations': ['dc101'],

                'data':
                    [['nextPageToken', 'token'], ['template', 'playlist'], ['offset', '0'],
                     ['limit', '150000'], ],
                'headers': {
                    'DNT': '1',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                },
                'next_headers': {
                    'origin': 'https://{}.iheart.com',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'en-US,en;q=0.8',
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'accept': 'text/html, */*; q=0.01',
                    'referer': 'https://{}.iheart.com/gmusic/recently-played/',
                    'dnt': '1',
                },
                'url': 'https://{}.iheart.com/gmusic/recently-played/',
                'next_url': 'https://{}.iheart.com/api/gmusic/load_more/'
            }
        }

    def get_iso_time(self, interval):

        now = datetime.now()
        for i in range(0, self.steps):
            t = now.replace(microsecond=0) - timedelta(hours=interval, minutes=randint(0, 9))
            yield t.isoformat()
            now = t

    def wrapper(self, func, interval):
        """ Coroutine wrapper"""

        yield from func(interval)

    def parse_cbs_station_data(self, data):
        """ Adds songs to list for cbs stations """

        for each_data in data:
            box_data = box.Box(each_data)
            for each_song in box_data.data.recentEvents:
                self.music_list.append([each_song.artist, each_song.title])

    def parse_tunegenie_data(self, data):
        """ Adds songs to list for tunegenie stations"""

        for each in data:
            mbox = box.Box(each)
            for eachlist in mbox.response:
                if eachlist.artist.startswith('Weekdays,') or eachlist.artist.startswith(
                        "The Valley's") or eachlist.artist.startswith("Sundays,"):
                    continue
                self.music_list.append([eachlist.artist, eachlist.song])

    def run_synchronous_process(self):
        """ Routine to scrape recently played song title/artist info in synchronous mode"""

        box_radio_stations = box.Box(self.radio_stations)

        for station in box_radio_stations.iheart.stations:
            content = requests.get(box_radio_stations.iheart.url.format(station),
                                   headers=box_radio_stations.iheart.headers).content
            soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
            for songinfo in [each.attrs['alt'] for each in soup.find_all() if 'alt' in each.attrs]:
                songdetails = songinfo.split(' - ')[::-1]
                if songdetails[0].startswith("Hawaii's Alternative") or songdetails[0].startswith('STATION_LOGO') or \
                        songdetails[0].startswith('{{') or songdetails[0].startswith('iHeartRadio') or songdetails[
                    0].startswith('Sundays,'):
                    continue

                self.music_list.append(songdetails)

            token = \
                [each.attrs['data-nextpagetoken'] for each in soup.find_all() if 'data-nextpagetoken' in each.attrs][0]
            data = box_radio_stations.iheart.data
            interval = box_radio_stations.tunegenie.interval
            data[0][1] = token
            data[3][1] = interval
            url = box_radio_stations.iheart.next_url.format(station)

            box_radio_stations.iheart.next_headers.origin = box_radio_stations.iheart.next_headers.origin.format(
                station)
            iheart_next_content = requests.post(url, headers=box_radio_stations.iheart.next_headers, data=data).content
            next_soup = BeautifulSoup(iheart_next_content, 'html.parser', from_encoding='utf-8')
            for songinfo in [each.attrs['alt'] for each in next_soup.find_all() if 'alt' in each.attrs]:
                songdetails = songinfo.split(' - ')[::-1]
                if songdetails[0].startswith("Hawaii's Alternative") or songdetails[0].startswith('STATION_LOGO') or \
                        songdetails[0].startswith('{{') or songdetails[0].startswith('iHeartRadio') or songdetails[
                    0].startswith('Sundays,'):
                    continue

                self.music_list.append(songdetails)

    async def fetch(self, headers, url, client, params=None, station=None, until=None, since=None):
        """ Async fetch method to retrieve song data from urls
            :param headers: dict connection header
            :param url: string url
            :param client: Async client session object
            :param params: dict connection parameters
            :param station: string station name
            :param until: datetime time stamp
            :param since: datetime time stamp
            :returns coroutine json object
        """

        if station == 'tunegenie':
            if until:
                params[1][1] = until
            else:
                until = params[0][1]
            params[0][1], params[1][1] = since, until
        elif station == 'cbs_stations':
            params[2][1] = since

        async with client.get(url, params=params, headers=headers) as resp:
            assert resp.status == 200
            return await resp.json()

    async def run_loop(self, loop, headers, url, params=None, station=None, interval=None):
        """ Async run loop method to fetch data
            :param loop: Asyncio event loop
            :param headers: dict connection header
            :param url: string url
            :param params: dict connection parameters
            :param station: string station name
            :param interval: dict number of iterations to loop through
            :returns coroutine asyncio response
        """

        until = None
        wrap = None
        since = None
        if station == 'cbs_stations':
            if len(params[-1]) == 1:
                params[-1].append(self.timestamp)
            wrap = self.wrapper(self.get_iso_time, interval)

        elif station == 'tunegenie':
            wrap = self.wrapper(self.get_iso_time, interval)

        tasks = []
        async with aiohttp.ClientSession(loop=loop) as client:

            for i in range(self.steps):
                if station == 'cbs_stations':
                    since = next(wrap)

                elif station == 'tunegenie':
                    if self.timestamp is None:
                        until = datetime.now().replace(microsecond=0).isoformat()
                    since = next(wrap)
                task = asyncio.ensure_future(self.fetch(headers, url, client, params, station,
                                                        until=until if self.timestamp is None else None,
                                                        since=since))
                tasks.append(task)
                self.timestamp = until
            responses = await asyncio.gather(*tasks)
        return responses
