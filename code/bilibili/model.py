#!/usr/bin/python3
__all__ = ('User', 'Video', 'Auto')



import collections
import faker
import math
import requests
import time
import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions



F = faker.Faker()
Comment = collections.namedtuple('Comments', ('content', 'like', 'user_id', 'timestamp'))



class User:
    '''User model

    API:
        - property
            - videos: iterator
            - number_of_videos: int
    '''

    _URL_VIDEO = 'https://api.bilibili.com/x/space/arc/search'
    _URL_FOLLOWER = 'https://api.bilibili.com/x/relation/followers'
    _URL_FOLLOWING = 'https://api.bilibili.com/x/relation/followings'

    def __init__(self, id, info=True):
        self.id = int(id)
        self._headers = {
            'host': 'api.bilibili.com',
            'referer': 'https://www.bilibili.com',
            'user-agent': F.user_agent(),
        }
        self.info = self._find_info() if info else None


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


    def _data(self, url, count, ps, order, id_name, keys1, key2):
        page_number = math.ceil(count/ps)
        f, g = self._ids_at, self._data_at
        return (f(g(url, page+1, ps, order, id_name), keys1, key2) for page in range(page_number))


    def _data_at(self, url, page, ps, order, id_name):
        params = dict(ps=ps, pn=page, order=order)
        params[id_name] = self.id
        response = requests.get(url, params=params, headers=self._headers)
        return response.json()


    def _ids_at(self, data, keys1, key2):
        for key in keys1:
            data = data[key]
        for video in data:
            yield video[key2]


    def _find_info(self):
        info = dict()
        # account info
        params = dict(mid=self.id, jsonp='jsonp')
        url = 'https://api.bilibili.com/x/space/acc/info'
        response = requests.get(url, params=params, headers=self._headers)
        data = response.json().get('data')
        for key in ('name', 'sex', 'face', 'sign', 'level', 'birthday'):
            info[key] = data.get(key)
        # up status
        url = 'https://api.bilibili.com/x/space/upstat'
        response = requests.get(url, params=params, headers=self._headers)
        data = response.json().get('data')
        info['archive_view'] = data.get('archive').get('view')
        info['article_view'] = data.get('article').get('view')
        info['likes'] = data.get('likes')
        # relation status
        params = dict(vmid=self.id, jsonp='jsonp')
        url = 'https://api.bilibili.com/x/relation/stat'
        response = requests.get(url, params=params)
        data = response.json().get('data')
        info['following'] = data.get('following')
        info['follower'] = data.get('follower')
        # return value
        return info



class Video:
    '''Video model

    API:
        - comments, iterator, all comments info
    '''
    def __init__(self, id, info=True):
        self.id = id
        self._headers = {
            'host': 'api.bilibili.com',
            'referer': 'https://www.bilibili.com',
            'user-agent': F.user_agent(),
        }
        self._timestamp = int(1000*time.time())
        if info:
            self.info = self._find_info()


    def __repr__(self):
        return f'<Video({self.info["title"]}) @ View {self.info["view"]}>'


    @property
    def comments(self):
        '''
        Format:
            - (content, like, user_id, timestamp)
        '''
        for page in self._comments(): 
            yield from page


    def _comments(self):
        first_page = self._comments_data_at(1)
        if first_page['data']:
            page_info = first_page['data']['page']
            page_number = math.ceil(page_info['count']/page_info['size'])
            f, g = self._find_comments, self._comments_data_at
            return (f(g(page+1)['data']['replies'])
                for page in range(page_number))
        return [[]]


    def _comments_data_at(self, page, root=0, ps=10, sort=2):
        url = 'https://api.bilibili.com/x/v2/reply'
        params = dict(pn=page, type=1, oid=self.id, sort=sort, _=self._timestamp)
        if root:
            url += '/reply'
            params.update(dict(root=root, ps=ps))
        return requests.get(url, params=params, headers=self._headers).json()


    def _find_comments(self, replies, ps=10):
        if replies:
            for reply in replies:
                message = reply['content']['message']
                mid = reply['member']['mid']
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
        response = requests.get(url, params=dict(aid=self.id))
        data = response.json().get('data')
        for key in ('pic', 'title', 'pubdate', 'desc', 'duration'):
            info[key] = data.get(key)
        info['owner'] = data['owner']['mid']
        # stat info
        stat = data['stat']
        for key in ('view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like'):
            info[key] = stat.get(key)
        return info



class Auto:
    _HOME = 'https://www.bilibili.com'
    _SPACE = 'https://space.bilibili.com'


    def __init__(self, login=True, web_driver='Chrome'):
        # set browser
        if isinstance(web_driver, str):
            self._browser = getattr(webdriver, web_driver)()
        elif isinstance(web_driver, webdriver.Remote):
            self._browser = web_driver
        else:
            raise TypeError('Argument `web_driver` has wrong type.')
        # login
        self._goto(self._HOME)
        if login:
            self.login()


    def __repr__(self):
        return f'<Auto @ {hash(self):#x}>'


    def login(self):
        '''Since I am lazy to write this function, you may login your
        Bilibili account manually.
        '''
        while self._browser.find_elements_by_class_name('logout-face'):
            input('(Off-line) Please log in >>> ')
        print('(On-line) You are now logged in.')


    def like_videos_from_user_in_video_comments(self, video_id):
        '''从视频评论区获得用户，点赞其投稿视频
        '''
        users = set()
        v = Video(video_id)
        for comment in v.comments:
            if comment.user_id not in users:
                users.add(comment.user_id)
                self.like_videos_from_user(comment.user_id)


    def like_videos_from_user(self, user_id):
        for video in User(user_id).videos:
            self._goto(self._video_url_from_id(video.id))
            # self._wait(element_to_be_clickable=(By.CLASS_NAME, class_like))
            self.like_this_video()


    def like_this_video(self):
        class_like = 'van-icon-videodetails_like'
        class_flag = 'like.on'
        self._browser.implicitly_wait(10)
        if not self._browser.find_elements_by_class_name(class_flag):
            element = self._browser.find_element_by_class_name(class_like)
            element.click()


    def _goto(self, url):
        self._browser.get(url)


    def _wait(self, timeout=5, poll_frequency=0.5, **kwargs):
        '''Web driver wait.

        Argument:
            - timeout: [int, float]
            - poll_frequency: [int, float]

        Example:
            >>> self._wait(element_to_be_clickable=(By.ID, '...'))
        '''
        wait =  WebDriverWait(self._browser, timeout, poll_frequency)
        for key, val in kwargs.items():
            wait.until(getattr(expected_conditions, key)(val))


    def _user_url_from_id(self, id):
        return self._SPACE + f'/{id}'


    def _video_url_from_id(self, id):
        return self._HOME + f'/av{id}'



if __name__ == '__main__':
    u = User(546195)
    vs = u.videos
    print(next(vs))

    v = Video(70885948)
    cs = v.comments
    print(next(cs))

    u = User(354576498, False)
