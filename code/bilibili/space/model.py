__all__ = ('User', 'Video', 'Dynamic', 'Comment')



import collections
import faker
import math
import requests
import time
import warnings



F = faker.Faker()
Comment = collections.namedtuple('Comments', ('content', 'like', 'user_id', 'timestamp'))



class User:
    '''User model

    API:
        - property
            - videos: iterator
            - number_of_videos: int
            - followers: iterator
            - number_of_followers: int
            - followings: iterator
            - number_of_followings: int
            + dynamics: itertor, to be done
            + channels: NotImplementedError
            + favorites: NotImplementedError
        - function
            - set_info()
            - set_cookies(cookies: dict)
            - set_cookies_from_selenium(webdriver: selenium.webdriver.Remote)
    '''

    _URL_VIDEO = 'https://api.bilibili.com/x/space/arc/search'
    _URL_FOLLOWER = 'https://api.bilibili.com/x/relation/followers'
    _URL_FOLLOWING = 'https://api.bilibili.com/x/relation/followings'

    def __init__(self, id, info=True):
        self.id = int(id)
        self._session = requests.Session()
        self._session.headers.update({
            'host': 'api.bilibili.com',
            'referer': 'https://www.bilibili.com',
            'user-agent': F.user_agent(),
        })
        self.info = None
        info and self.set_info()


    def __repr__(self):
        if self.info:
            return f'<User("{self.info["name"]}") @ LV {self.info["level"]}>'
        else:
            return f'<User({self.id})>'


    @property
    def videos(self):
        '''Iterate all videos from user

        Example:
            >>> for video in user.videos:
            ...     print(video)
        '''
        url = self._URL_VIDEO
        count = self.number_of_videos
        keys1, key2 = ('data', 'list', 'vlist'), 'aid'
        for page in self._data(url, count, 30, 'pubdate', 'mid', keys1, key2):
            for id in page:
                yield Video(id)


    @property
    def number_of_videos(self):
        '''Return the number of videos
        '''
        data = self._data_at(self._URL_VIDEO, 1, 30, 'pubdate', 'mid')
        return data['data']['page']['count']


    @property
    def followers(self):
        '''Iterate all followers from user

        Example:
            >>> for follower in user.followers:
            ...     print(follower)
        '''
        url = self._URL_FOLLOWER
        count = self.number_of_followers
        keys1, key2 = ('data', 'list'), 'mid'
        for page in self._data(url, count, 20, 'desc', 'vmid', keys1, key2):
            for id in page:
                yield User(id, self.info is not None)


    @property
    def number_of_followers(self):
        '''Return the number of followers
        '''
        data = self._data_at(self._URL_FOLLOWER, 1, 20, 'desc', 'vmid')
        return data['data']['total']


    @property
    def followings(self):
        '''Iterate all followings from user

        Example:
            >>> for following in user.followings:
            ...     print(following)
        '''
        url = self._URL_FOLLOWING
        keys1, key2 = ('data', 'list'), 'mid'
        count = self.number_of_followings
        for page in self._data(url, count, 20, 'desc', 'vmid', keys1, key2):
            for id in page:
                yield User(id, self.info is not None)


    @property
    def number_of_followings(self):
        '''Return the number of followings
        '''
        data = self._data_at(self._URL_FOLLOWING, 1, 20, 'desc', 'vmid')
        return data['data']['total']


    @property
    def dynamics(self):
        '''Iterable all dynamics
        '''
        # warnings.warn('Dynamics have complex types, to be done.', Warning)
        for dynamic in self._dynamics():
            desc = dynamic.pop('desc')
            yield Dynamic.from_args(
                id=desc['dynamic_id'], user_id=desc['uid'], view=desc['view'],
                repost=desc['repost'], number_of_comments=desc['comment'],
                like=desc['like'], timestamp=desc['timestamp'], others=desc,
            )


    @property
    def channels(self):
        raise NotImplementedError


    @property
    def favorites(self):
        raise NotImplementedError


    def set_info(self):
        '''Set information of current user
        '''
        if not self.info:
            self.info = self._find_info()


    def set_cookies(self, cookies):
        '''Set cookies of current session with `cookies`
        '''
        self._session.cookies.update(cookies)


    def set_cookies_from_selenium(self, webdriver):
        '''Set cookies from `selenium`
        '''
        cookies = webdriver.get_cookies()
        self.set_cookies({item['name']: item['value'] for item in cookies})


    def _data(self, url, count, ps, order, id_name, keys1, key2):
        page_number = math.ceil(count/ps)
        f, g = self._ids_at, self._data_at
        return (
            f(g(url, page+1, ps, order, id_name), keys1, key2)
                for page in range(page_number)
        )


    def _data_at(self, url, page, ps, order, id_name):
        params = dict(ps=ps, pn=page, order=order)
        params[id_name] = self.id
        response = self._session.get(url, params=params)
        return response.json()


    def _ids_at(self, data, keys1, key2):
        try:
            for key in keys1:
                data = data[key]
            for video in data:
                yield video[key2]
        except KeyError:
            warnings.warn('Unauthenticated access cannot get more information, ' \
                'please login by selenium.', Warning)
            return None


    def _dynamics(self):
        url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history'
        params = dict(host_uid=self.id, offset_dynamic_id=0)
        while True:
            response = requests.get(url, params=params)  # do not use `self._session`
            data = response.json()['data']
            yield from data['cards']
            if not data['has_more']:
                break
            params['offset_dynamic_id'] = data['next_offset']


    def _find_info(self):
        info = dict()
        # account info
        params = dict(mid=self.id, jsonp='jsonp')
        url = 'https://api.bilibili.com/x/space/acc/info'
        response = self._session.get(url, params=params)
        data = response.json().get('data')
        for key in ('name', 'sex', 'face', 'sign', 'level', 'birthday'):
            info[key] = data.get(key)
        # up status
        url = 'https://api.bilibili.com/x/space/upstat'
        response = self._session.get(url, params=params)
        data = response.json().get('data')
        info['archive_view'] = data.get('archive').get('view')
        info['article_view'] = data.get('article').get('view')
        info['likes'] = data.get('likes')
        # relation status
        params = dict(vmid=self.id, jsonp='jsonp')
        url = 'https://api.bilibili.com/x/relation/stat'
        response = self._session.get(url, params=params)
        data = response.json().get('data')
        info['following'] = data.get('following')
        info['follower'] = data.get('follower')
        # return value
        return info



class Video:
    '''Video model

    API:
        - property
            - comments, iterator
        - function
            - set_info()
    '''

    def __init__(self, id, info=True):
        self.id = int(id)
        self._session = requests.Session()
        self._session.headers.update({
            'host': 'api.bilibili.com',
            'referer': 'https://www.bilibili.com',
            'user-agent': F.user_agent(),
        })
        self._timestamp = int(1000*time.time())
        self.info = None
        info and self.set_info()


    def __repr__(self):
        if self.info:
            return f'<Video({self.info["title"]}) @ {self.info["view"]}>'
        else:
            return f'<Video({self.id})>'


    @property
    def comments(self):
        '''
        Example:
            >>> for comment in video.comments:
            ...     print(comment)
        '''
        for page in self._comments(): 
            yield from page


    def set_info(self):
        if not self.info:
            self.info = self._find_info()


    def _comments(self, type=1):
        first_page = self._comments_data_at(1, type=type)
        if first_page['data']:
            page_info = first_page['data']['page']
            page_number = math.ceil(page_info['count']/page_info['size'])
            f, g = self._find_comments, self._comments_data_at
            return (f(g(page+1, type=type)['data']['replies'])
                for page in range(page_number))
        return list(list())


    def _comments_data_at(self, page, root=0, ps=10, sort=2, type=1):
        url = 'https://api.bilibili.com/x/v2/reply'
        params = dict(pn=page, type=type, oid=self.id, sort=sort, _=self._timestamp)
        if root:
            url += '/reply'
            params.update(dict(root=root, ps=ps))
        return self._session.get(url, params=params).json()


    def _find_comments(self, replies, ps=10):
        if replies:
            for reply in replies:
                message = reply['content']['message']
                mid = int(reply['member']['mid'])
                ctime = reply['ctime']
                like = reply['like']
                yield Comment(message, like, mid, ctime)
                rcount = reply['rcount']
                if rcount:
                    for page in range(math.ceil(rcount/ps)):
                        rpid = reply['rpid']
                        data = self._comments_data_at(page+1, rpid, ps)
                        replies = data['data']['replies']
                        yield from self._find_comments(replies)


    def _find_info(self):
        info = dict()
        # video info
        url = 'https://api.bilibili.com/x/web-interface/view'
        response = self._session.get(url, params=dict(aid=self.id))
        data = response.json().get('data')
        for key in ('pic', 'title', 'pubdate', 'desc', 'duration'):
            info[key] = data.get(key)
        info['owner'] = data['owner']['mid']
        # stat info
        stat = data['stat']
        for key in ('view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like'):
            info[key] = stat.get(key)
        return info



class Dynamic:
    '''Dynamic model

    API:
        - property
            - comments, iterator
            - number_of_comments, int
        - function
            - set_info()
    '''

    def __init__(self, id, info=True):
        self.id = int(id)
        info and self.set_info()


    def __repr__(self):
        view = getattr(self, 'view', 'None')
        return f'<Dynamic({self.id} @ View {view})>'


    @classmethod
    def from_args(cls, id, **kwargs):
        self = cls(id, False)
        keys = ('user_id', 'view', 'repost', 'number_of_comments', 'like', 'timestamp')
        for key in keys:
            setattr(self, key, kwargs.get(key, None))
        self.others = kwargs.get('others', None)
        return self


    @property
    def comments(self):
        pass


    def set_info(self):
        url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail'
        params = dict(dynamic_id=self.id)
        data = requests.get(url, params=params).json()['data']['card']['desc']
        keys = ('view', 'repost', 'like', 'timestamp')
        for key in keys:
            setattr(self, key, data.get(key, None))
        self.number_of_comments = data['comment']



if __name__ == '__main__':
    u = User(546195)
    v = next(u.videos)
    c = next(v.comments)
    fer = next(u.followers)
    fing = next(u.followings)

    print('User:', u)
    print('Video:', v)
    print('Comment:', c)
    print('Follower:', fer)
    print('Following:', fing)
