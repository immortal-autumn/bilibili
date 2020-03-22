#!/usr/bin/python3
import collections
import requests



LiveRoom = collections.namedtuple('LiveRoom', ('id', 'name', 'online', 'area'))



class LiveByArea:
    '''Live model of Bilibili.

    Argument:
        - id: [int, str], tag id, default is 27 (study area)
    '''
    def __init__(self, id=27):
        self.id = id


    def __repr__(self):
        return f'<Live @ {hash(self):#x}>'


    @property
    def urls(self):
        for room in self._get_rooms():
            yield f'https://live.bilibili.com/{room.id}'


    @property
    def rooms(self):
        yield from self._get_rooms()


    def _get_rooms(self, pn=30):
        keys = ('roomid', 'uname', 'online', 'area_name')
        url = 'https://api.live.bilibili.com/room/v3/area/getRoomList'
        params = dict(area_id=self.id, page=1, page_size=pn)
        response = requests.get(url, params=params)
        data = response.json()['data']
        count = data['count']
        while count:
            for room in data['list']:
                count -= 1
                yield LiveRoom(*(room[key] for key in keys))
            params['page'] += 1
            data = requests.get(url, params=params).json()['data']
