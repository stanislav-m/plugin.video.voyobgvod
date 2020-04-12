# -*- coding: utf-8 -*-
import time
import requests
import random
import re
import base64
import json
from bs4 import BeautifulSoup
import sys

class voyo_web_api:
    def __init__(self, settings):
        requests.packages.urllib3.disable_warnings()
        self.__settings = settings
        self.__ses = requests.session()
        self.__res = 0

    def __parse_par(self, regex, txt):
        x = re.search(regex, txt)
        if x:
            return x.group(1)
        else:
            return ''

    def login(self):
        body = { "username": self.__settings['username'], "password": self.__settings['password']}
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        self.__res = self.__ses.post('https://voyo.bg/bin/eshop/ws/user.php?x=login&r={0}'.format(
            random.random()),
            headers=headers, data=body, verify=False)
        if self.__res.status_code == 200:
            j = self.__res.json()
            return j['logged']
        return False

    def __user(self, productid, unitid):
        body = { "productId": productid, "unitId": unitid, 'x': 'userStatus'}
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        self.__res = self.__ses.post('https://voyo.bg/bin/eshop/ws/user.php', headers=headers, data=body)
        if self.__res.status_code == 200:
            j = self.__res.json()
            return j['loggedIn']
        return False

    def __user_data(self):
        self.__res = self.__ses.post('https://voyo.bg/bin/eshop/ws/user.php?x=userData&r={0}'.format(
			random.random()))
        if self.__res.status_code == 200:
            j = self.__res.json()
            return j['loggedIn']
        return False

    def __is_logged_in(self):
        self.__res = self.__ses.post('https://voyo.bg/bin/eshop/ws/user.php?x=isLoggedIn&r={0}'.format(random.random()))
        if self.__res.status_code == 200:
            return self.__res.text == 'true'
        return False

    def __user_can_consume(self, product):
        self.__res = self.__ses.post('https://voyo.bg/bin/eshop/ws/user.php?x=canConsume&prod={0}&dev={1}&r={2}'.format(
			product, self.__settings['device'], random.random()))
        if self.__res.status_code == 200:
            j = self.__res.json()
            return j['can']
        return False

    def __user_ppv_status(self):
        self.__res = self.__ses.post('https://voyo.bg/lbin/eshop/ws/user_ppv_status.php?&r={0}'.format(random.random()))
        if self.__res.status_code == 200:
            return self.__res.text == 'true'
        return False

    def __user_info(self):
        self.__res = self.__ses.post('https://voyo.bg/lbin/eshop/ws/ewallet.php?x=userInfo')
        if self.__res.status_code == 200:
            j = self.__res.json()
            self.__username = j['Username']
            return True
        return False

    def __visitor(self):
        self.__res = self.__ses.post('https://voyo.bg/lbin/global/visitor.php')
        if self.__res.status_code == 200:
            j = self.__res.json()
            return j['user']
        return False

    def __user_registration(self):
        self.__res = self.__ses.post('https://voyo.bg/bin/registration2/user_info.php')
        if self.__res.status_code == 200:
            jres = self.__res.json()
            return True
        return False

    def list_devices(self):
        devices = []
        self.__res = self.__ses.post('https://voyo.bg/profil/?sect=devices')
        if self.__res.status_code == 200:
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            dev_nav = soup.find_all('div', class_='device')
            for dev in dev_nav:
                act = dev.find('div', class_='active')
                a = dev.find('a')
                x = re.search('removeDevice\((\\d+)\)', a['onclick'])
                devices.append((dev.div.h1.text.encode(self.__res.encoding),
                                        dev.div.h2.text.encode(self.__res.encoding),
                                       act.text.encode(self.__res.encoding), x.group(1)))
        return devices

    def device_allowed(self):
        url = 'https://voyo.bg/bin/eshop/ws/ewallet.php?\
x=device&a=isAllowed&deviceHash={0}&r={1}'.format(self.__settings['device'], random.random())
        self.__res = self.__ses.post(url)
        if self.__res.status_code == 200:
            return self.__res.json()['ok']
        return False

    def device_add(self):
        url = 'https://voyo.bg/bin/eshop/ws/ewallet.php?x=device&a=add&deviceCode=PC&deviceHash={0}\
&client={1}"b":"S","bv":"537.36","ua":"Mozilla/5.0 (X11; Linux x86_64) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"{2}\
&r={3}'.format(self.__settings['device'], '{', '}', random.random())
        self.__res = self.__ses.post(url)
        if self.__res.status_code == 200:
            return self.__res.json()['ok']
        return False

    def __get_product_url(self, product, unit, media, site, section, device):
        url = 'https://voyo.bg/lbin/eshop/ws/plusPlayer.php?\
x=streamStat&prod={0}&unit={1}&media={2}&site={3}&section={4}&subsite=product&\
embed=0&mute=0&size=&realSite={5}&width=995&height=604&hash=&dev={6}&\
finish=finishedPlayer&streamQuality=NaN&imsz=711x448&r={7}'.format(
                product, unit, media, site, section, site, device, random.random()
            )
        self.__res = self.__ses.post(url)
        if self.__res.status_code == 200:
            j = self.__res.json()
            if j['status'] == 'PLAYING':
                html = j['html']
                sp = BeautifulSoup(html, 'html.parser')
                src = sp.find('source')
                if src:
                    return src['src']
        return ''

    def __plus_player_default(self, product, unit, device):
        url = 'https://voyo.bg/lbin/eshop/ws/plusPlayer.php?\
x=default&prod={0}&unit={1}&width=995&height=604&imsz=995x604&dev={2}&wv=0&r={3}'.format(
                product, unit, device, random.random()
            )
        self.__res = self.__ses.post(url)
		#no responce

    def __get_shaka_params(self, src):
        s_patt = {
            'poster_url' : "var posterUrl = 'http://voyo.bg/(.+)';",
            'license_url' : "'lsu': '(.+)',",
            'play_url' : "'url': '(.+)',"
        }
        pl_par = {}
        for key in s_patt:
            pl_par[key] = self.__parse_par(s_patt[key], src)
        return pl_par

    def __get_vod_url(self, product, unit, media, site, section, device):
        #if not self.device_add():
        #    return ''

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en;q=0.9,bg-BG;q=0.8,bg;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
			'Host': 'voyo.bg',
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
			'X-Requested-With': 'XMLHttpRequest'
            }

        url = 'https://voyo.bg/lbin/eshop/ws/plusPlayer.php?\
x=playerFlash&prod={0}&unit={1}&media={2}&site={3}&section={4}&subsite=product&\
embed=0&mute=0&size=&realSite={5}&width=995&height=604&hash=&finish=finishedPlayer&dev={6}&\
wv=0&sts=undefined&formatQuality=null&r={7}'.format(
                product, unit, media, site, section, site, device, random.random()
            )
        self.__res = self.__ses.post(url, headers=headers)
        if self.__res.status_code == 200:
            j = self.__res.json()
            if not j['error']:
                html = j['html']
                sp = BeautifulSoup(html, 'html.parser')
                jscript = sp.find_all('script')
                for js in jscript:
                    if 'src' not in js:
                        if len(js.text.encode(self.__res.encoding)) > 0:
                            return self.__get_shaka_params(js.text)
        return ''

    def device_remove(self, dev_id):
        url = 'https://voyo.bg/bin/eshop/ws/ewallet.php?\
x=device&a=remove&id={0}r={1}'.format(dev_id, random.random())
        self.__res = self.__ses.post(url)
        if self.__res.status_code == 200:
            return self.__res.json()['ok']
        return False

    def sections(self):
        sect_list = []
        self.__res = self.__ses.post('https://voyo.bg')
        if self.__res.status_code == 200:
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            prod_nav = soup.find(id='product_navigation')
            cat = prod_nav.ul.find_all('a')
            for c in cat:
                name = c.text.encode(self.__res.encoding)
                if len(name.strip()) > 0:
                    sect_list.append((name, c['href']))
        return sect_list

    def tv_radio(self, href):
        url = 'https://voyo.bg{0}'.format(href)
        self.__res = self.__ses.post(url)
        channel_list = []
        if self.__res.status_code == 200:
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            channels = soup.find_all('div', class_= re.compile("^online-channels"))
            for chan in channels:
                item_list = chan.find_all('li')
                for it in item_list:
                    name = it['class'][0]
                    link = it.a['href']
                    img = 'https://voyo.bg{0}'.format(it.a.div.img['src'])
                    play_url = self.channel_url(link)
                    channel_list.append((name, url, img, play_url))
        return channel_list

    def __play_link(self, soup):
        play_cover = soup.find('div', class_='cover-play-video')
        if play_cover:
            pl = play_cover.find('a',
                                 onclick="playVideoOnFullScreen('main'); return false;")
            if pl:
                return True
        return False

    def __player_params(self, soup):
        s_patt = {
            'section' : 'ut_section_id = .(\\d+).;',
            'site' : 'site_id = .(\\d+).;',
            'section_id' : 'section_id = .(\\d+).;',
            'product' : 'product_id = .(\\d+).;',
            'unit' : 'unit_id = .(\\d+).;'
        }
        par_fnd = False
        med_fnd = False
        pl_par = {}
        jscript = soup.find_all('script', language="JavaScript1.1", type="text/javascript")
        for js in jscript:
            if js.text.find('var ut_section_id =') > 0:
                for key in s_patt:
                    pl_par[key] = self.__parse_par(s_patt[key], js.text)
                par_fnd = True
            elif js.text.find('mainVideo = new mediaData(') > 0:
                pl_par['media'] = self.__parse_par('mainVideo = new mediaData\(\\d+, \\d+, (\\d+),', js.text)
                med_fnd = True
            if med_fnd and par_fnd:
                break
        return pl_par

    def channel_url(self, href):
        url = 'https://voyo.bg{0}'.format(href)
        self.__res = self.__ses.post(url)
        media = ''
        if self.__res.status_code == 200:
            whole_page = self.__res.text.encode('utf-8')
            if whole_page.find('mainVideo = new mediaData('):
                media = self.__parse_par('mainVideo = new mediaData\(\\d+, \\d+, (\\d+),',
                                     whole_page)
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            pl_par = self.__player_params(soup)
            if not self.device_allowed():
                if not self.device_add():
                    return None
            return self.__get_product_url(pl_par['product'], pl_par['unit'], media,
                pl_par['site'], pl_par['section'], self.__settings['device'])

    def process_play_url(self, href):
        self.__res = self.__ses.post(href)
        product_list = []
        if self.__res.status_code == 200:
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            pl_par = self.__player_params(soup)
            if not self.device_allowed():
                if not self.device_add():
                    return None
            if self.__play_link(soup):
                if self.__user_can_consume(pl_par['product']):
                    return self.__get_vod_url(pl_par['product'], pl_par['unit'], pl_par['media'],
                        pl_par['site'], pl_par['section'], self.__settings['device'])
            return None

    def __find_meta(self, soup):
        meta = soup.find_all('meta', property=re.compile('^og'))
        title = ''
        img = ''
        url = ''
        plot = ''
        for m in meta:
            if m['property'] == "og:title":
                title = m['content']
            elif m['property'] == "og:image":
                img = m['content']
            elif m['property'] == "og:url":
                url = m['content']
            elif m['property'] == "og:description":
                plot = m['content']

        meta_info = {}
        cls_descr = soup.find('div', class_='description')
        if cls_descr != None:
            sp = cls_descr.find_all('span')
            extra_attr = {}
            for c in sp:
                for k in c.attrs:
                    v = c[k]
                    extra_attr[v[0].encode(self.__res.encoding)] = c.text.encode(self.__res.encoding)
            for k in extra_attr:
                v = extra_attr[k]
                if k == 'genres':
                    meta_info['genre'] = ' '.join(v.split()).strip()
                elif k == 'country':
                    meta_info[k] = v
                elif k == 'label':
                    meta_info['rating'] = (float(v)*10)/5
                elif k == 'year':
                    meta_info[k] = v.split()[0]
                elif k == 'duration':
                    meta_info[k] = int(v.split()[0]) * 60
            if len(plot) > 0:
                meta_info['plot'] = plot.encode(self.__res.encoding)

        return (title.encode(self.__res.encoding),
                url.encode(self.__res.encoding).replace('http://', 'https://'),
                img.encode(self.__res.encoding),
                plot.encode(self.__res.encoding), meta_info)

    def __process_series(self, soup):
        ps = soup.find('div', class_=re.compile('^productsList'))
        series = ps.find_all('li', class_='item')
        products = []
        for item in series:
            name = item.div.a.img['title'].encode(self.__res.encoding)
            link = item.div.a['href']
            img = item.div.a.img['src']
            products.append((name, link, img))
        title, url, img, plot, meta_info =  self.__find_meta(soup)
        return products, meta_info

    def __play_title(self, soup):
        return self.__find_meta(soup)
        #return (title.encode(self.__res.encoding),
        #        url.encode(self.__res.encoding).replace('http://', 'https://'),
        #        img.encode(self.__res.encoding),
        #        plot.encode(self.__res.encoding), meta_info)

    def list_series(self, href):
        url = 'https://voyo.bg{0}'.format(href)
        self.__res = self.__ses.post(url)
        product_list = []
        if self.__res.status_code == 200:
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            return self.__process_series(soup)

    def process_page(self, href):
        url = 'https://voyo.bg{0}'.format(href)
        self.__res = self.__ses.post(url)
        if self.__res.status_code == 200:
            soup = BeautifulSoup(self.__res.text, 'html.parser')
            check_player = soup.find('div', class_='video-player-wrap-middle')
            if check_player == None:
                return self.__process_series(soup)
            else:
                title, url_ref, img, plot, metadt =  self.__play_title(soup)
                play_params = self.process_play_url(url_ref)
                return title, url_ref, img, plot, metadt, play_params
