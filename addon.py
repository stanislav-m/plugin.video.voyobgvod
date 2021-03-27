# -*- coding: utf-8 -*-
import sys
import os
import threading
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
from bs4 import BeautifulSoup
from resources.lib.voyo_web_api import *
from resources.lib.epgprocess import *
if sys.version_info[0] > 2 or sys.version_info[0] == 2 and sys.version_info[1] >= 7:
    import inputstreamhelper
    tv_only = False
else:
    tv_only = True
if sys.version_info[0] == 2:
    from urllib import urlencode
    from urllib import quote_plus
    from urlparse import parse_qsl
else:
    from urllib.parse import urlencode
    from urllib.parse import quote_plus
    from urllib.parse import parse_qsl
import uuid
import json
import codecs

config_par = ['username', 'password', 'device', 'useEPG', 'epgURL',
              'epgOffset', 'wrkdir' ]
settings = {}

_url = sys.argv[0]
_handle = int(sys.argv[1])
__addon__   = xbmcaddon.Addon()

def get_addon():
  return __addon__

def get_addon_id():
  return __addon__.getAddonInfo('id')

def get_addon_name():
  return __addon__.getAddonInfo('name').decode('utf-8')

def get_addon_version():
  return __addon__.getAddonInfo('version')

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def getUrl(keyval_pair):
    return '{0}?{1}'.format(_url, urlencode(keyval_pair))

def get_platform():
  platforms = [
    "Android",
    "Linux.RaspberryPi",
    "Linux",
    "XBOX",
    "Windows",
    "ATV2",
    "IOS",
    "OSX",
    "Darwin"
   ]

  for platform in platforms:
    if xbmc.getCondVisibility('System.Platform.{0}'.format(platform)):
      return platform
  return "Unknown"

def get_version():
    return xbmc.getInfoLabel("System.BuildVersion")

def get_prn(msg):
    if str(type(msg)) == "<type 'unicode'>":
        s = msg.encode('utf-8')
    else:
        s = str(msg)
    return s

def log_primitive(msg, level):
    if str(type(msg)) == "<type 'unicode'>":
        s = msg.encode('utf-8')
    else:
        s = str(msg)
    xbmc.log("{0} v{1} | {2}".format(get_addon_id(), get_addon_version(), s), level)

def log(msg, level=xbmc.LOGDEBUG):
    try:
        level = xbmc.LOGNOTICE
        if str(type(msg)) == "<type 'list'>" or str(type(msg)) == "<type 'tuple'>":
            for m in msg:
                log_primitive(msg, level)
        elif str(type(msg)) == "<type 'dict'>":
            for key in msg:
                log_primitive('{0} : {1}'.format(
                    get_prn(key), get_prn(msg[key])), level)
        else:
            log_primitive(msg, level)

    except:
        try:
            import traceback
            er = traceback.format_exc(sys.exc_info())
            xbmc.log('%s | Logging failure: %s' % (get_addon_id(), er), level)
        except:
            pass

class voyobg:
    def __init__(self):
        self.__api = voyo_web_api(settings)

    def login(self):
        return self.__api.login()

    def get_devices(self):
        return self.__api.list_devices()

    def check_device(self):
        return self.__api.device_allowed() or self.__api.device_add()

    def remove_device(self, dev_id):
        return self.__api.device_remove(dev_id)

    def sections(self):
        return self.__api.sections()

    def tv_radio(self, href):
        return self.__api.tv_radio(href)

    def channel(self, href):
        return self.__api.channel_url(href)

    def series(self, href):
        return self.__api.list_series(href)

    def process_page(self, href):
        return self.__api.process_page(href)

    def process_play_url(self, href):
        return self.__api.process_play_url(href)


class voyo_plugin:
    def __init__(self):
        if sys.version_info[0] == 2:
            self.wrkdir = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode('utf-8')
        else:
            self.wrkdir = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
        self.getSettings()
        if 'wrkdir' in settings:
            swd = settings['wrkdir']
            if len(swd) > 0:
                self.wrkdir = swd
        log('workdir: {0}'.format(self.wrkdir))
        self.useEPG = settings['useEPG'].lower() == 'true'
        self.epgOffset = int(settings['epgOffset'])
        self.voyo = voyobg()
        if not tv_only and self.useEPG: #python 2.6 won't be able to download the epg
            self.epg = voyo_epg(self.wrkdir)
            self.epg.configure(self.wrkdir, settings['epgURL'], self.epgOffset)
            self.epg.run()
        loginAttemps = 0
        while not self.voyo.login() and loginAttemps < 3:
            loginAttemps += 1
            dialog = xbmcgui.Dialog()
            dialog.ok(u'Грешка', u'Некоректни данни за абонамент!')
            __addon__.openSettings()
            self.getSettings()

        logofname = '{0}logos.json'.format(self.wrkdir)
        if xbmcvfs.exists(logofname):
            with open(logofname, 'r') as f:
                logostr = f.read()
                self.logos = json.loads(logostr)
        else:
            self.logos = {}

        epgfname = '{0}epg.json'.format(self.wrkdir)
        if xbmcvfs.exists(epgfname):
            with codecs.open(epgfname, 'r', 'utf-8') as f:
                epgs = f.read()
                self.epg = json.loads(epgs)
        else:
            self.epg = {}


    def getSettings(self):
        for key in config_par:
            settings[key] = __addon__.getSetting(key)
        if len(settings['username']) == 0 or len(settings['password']) == 0:
            __addon__.openSettings()
            settings['username'] = __addon__.getSetting('username')
            settings['password'] = __addon__.getSetting('password')
        if len(settings['device']) == 0:
            settings['device'] = uuid.uuid4().hex
            __addon__.setSetting('device', settings['device'])
        for key in config_par:
            settings[key] = __addon__.getSetting(key)
        log(settings)

    def list_categories(self):
        xbmcplugin.setPluginCategory(_handle, 'Voyobg')
        xbmcplugin.setContent(_handle, 'videos')
        categories = self.voyo.sections()
        for name, link in categories:
            if tv_only:
                if link != '/tv-radio/':
                    continue
            li = xbmcgui.ListItem(label=name)
            li.setInfo('video', {'title': name,
                                        'genre': 'Voyo content',
                                        'mediatype': 'video'})
            url = get_url(action='listing_sections', category=link.replace('/', '_'))
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)
        xbmcplugin.endOfDirectory(_handle)

    def list_item(self, name, link, img, plot, act_str, meta_inf=None):
        log('{0} :  {1} - {2}'.format(name, link, img))
        li = xbmcgui.ListItem(label=name)
        art = { 'thumb': img, 'poster': img, 'banner' : img, 'fanart': img }
        li.setArt(art)
        info_labels = {'title': name, 'plot': plot}
        if meta_inf:
            info_labels.update(meta_inf)
        li.setInfo('video', info_labels)
        ctxtmenu = []
        ctxtmenu.append(('Информация', 'XBMC.Action(Info)'))
        li.addContextMenuItems(ctxtmenu)
        #dict_url = {'action' : act_str, 'category': link.replace('/', '_'),
        #            'name' : name, 'img' : img, 'plot' : plot, 'link' :link}
        dict_url = {'action' : act_str, 'category': link.replace('/', '_')}
        if meta_inf:
            dict_url.update(meta_inf)
        isDir = True
        if act_str == 'listing_tv':
            dict_url['name'] = name
            isDir = False
        url = getUrl(dict_url)
        xbmcplugin.addDirectoryItem(_handle, url, li, isDir)

    def list_play_url(self, name, link, img, plot, meta_inf, play_param):
        log('{0} - {1}'.format(name, play_param['play_url']))
        if not (sys.version_info[0] > 2 or sys.version_info[0] == 2 and
                sys.version_info[1] >= 7):
            dialog = xbmcgui.Dialog()
            dialog.ok(
            u'Грешка',
            u'Вашето устройство не може да възпроизведе това видео.')
            return
        if play_param:
            headers = "User-agent: stagefright/1.2 (Linux;Android 6.0)"
            PROTOCOL = 'mpd'
            DRM = 'com.widevine.alpha'
            is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
            if is_helper.check_inputstream():
                metaflds = ['genre', 'country', 'rating', 'year', 'duration',
                            'plot']
                li = xbmcgui.ListItem(label=name, path=play_param['play_url'])
                inf_labels = {}
                for mf in metaflds:
                    if mf in meta_inf:
                        inf_labels[mf] = meta_inf[mf]
                li.setInfo(type="Video", infoLabels=inf_labels)
                li.setArt({'thumb': img, 'icon': img, 'fanart': img})
                if sys.version_info[0] == 2:
                    li.setProperty('inputstreamaddon', 'inputstream.adaptive')
                else:
                    li.setProperty('inputstream', 'inputstream.adaptive')
                li.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                li.setProperty('inputstream.adaptive.stream_headers', headers)
                li.setProperty('inputstream.adaptive.license_type', DRM)
                licURL = play_param['license_url'] + '||R{SSM}|BJBwvlic'
                li.setProperty('inputstream.adaptive.license_key', licURL)
                li.setProperty('inputstream.adaptive.media_renewal_time', '600')
                li.setMimeType('application/dash+xml')
                li.setProperty("IsPlayable", str(True))
                xbmcplugin.addDirectoryItem(_handle, play_param['play_url'], li)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(
            u'Грешка',
            u'Видеото не е налично.')

    def get_channel_epg(self, name, i):
        tvmapping = {
            'btv': "bTV", 'int': "bTVi", 'comedy': "bTVComedy",
            'cinema': "bTVCinema", 'action': "bTVAction", 'lady': "bTVLady",
            'ring': "RING", 'voyo-cinema':"VoyoCinema"
        }
        chan_epg = []
        epg_str = ''
        img = i
        if self.useEPG:
            if name in tvmapping:
                name = tvmapping[name]
            if name in self.logos:
                img = self.logos[name]
            if name in self.epg:
                chan_epg = self.epg[name]
            cnt = 0
            now = time.time()
            for it in chan_epg:
                start = time.mktime(
                    time.strptime(it[0].split()[0],'%Y%m%d%H%M%S'))
                stop = time.mktime(
                    time.strptime(it[1].split()[0],'%Y%m%d%H%M%S'))
                if sys.version_info[0] == 2:
                    title = it[2].encode('utf-8')
                else:
                    title = it[2]
                if (start < now and stop >= now) or (now < start):
                    cnt += 1
                    ln = '{0} {1}\n'.format(
                        time.strftime('%H:%M', time.localtime(start)),
                                            title)
                    epg_str += ln
                if cnt >= 8:
                    break
        return epg_str, img, name

    def play_tv(self, params):
        self.device_status()
        category = params['category']
        link = category.replace('_', '/')
        epg_name = params['name']
        name, img, play_url = self.voyo.channel(link)
        epg_str, img, n = self.get_channel_epg(epg_name, img)
        li = xbmcgui.ListItem(label=name, path=play_url)
        li.setInfo(type="Video", infoLabels={'genre':'TV',
            'plot':epg_str })
        li.setArt({'thumb': img, 'icon': img, 'fanart': img})
        li.setProperty("IsPlayable", str(True))
        if sys.version_info[0] > 2 or sys.version_info[0] == 2 and sys.version_info[1] >= 7:
            headers = "User-agent: stagefright/1.2 (Linux;Android 6.0)"
            PROTOCOL = 'hls'
            is_helper = inputstreamhelper.Helper(PROTOCOL)
            if is_helper.check_inputstream():
                if sys.version_info[0] == 2:
                    li.setProperty('inputstreamaddon', 'inputstream.adaptive')
                else:
                    li.setProperty('inputstream', 'inputstream.adaptive')
                li.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                li.setProperty('inputstream.adaptive.stream_headers', headers)
            else:
                log('inputstreamhelper check failed.')
        xbmc.Player().play(play_url, li)

    def list_content(self, params):
        self.device_status()
        category = params['category']
        cat_link = category.replace('_', '/')
        xbmcplugin.setPluginCategory(_handle, category)
        xbmcplugin.setContent(_handle, 'videos')
        if cat_link == '/tv-radio/':
            action_str = 'listing_tv'
            content = self.voyo.tv_radio(cat_link)
            for cont in content:
                name, link, img = cont
                epg_str, img, name = self.get_channel_epg(name, img)
                self.list_item(name, link, img, epg_str, action_str)
        else:
            ret = self.voyo.process_page(cat_link)
            if ret:
                if len(ret) == 2:
                    action_str = 'listing_sections'
                    content, meta = ret
                    for cont in content:
                        name, link, img = cont
                        self.list_item(name, link, img, '', action_str, meta)
                else:
                    name, link, img, plot, meta, play_param = ret
                    self.list_play_url(name, link, img, plot, meta, play_param)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(
                u'Грешка',
                u'Вашето устройство не може да възпроизведе това видео.')
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(_handle)

    def device_status(self):
        dialog = xbmcgui.Dialog()
        while not self.voyo.check_device():
            dialog.ok(
            u'Грешка',
            u'Достигнал си максималния брой устройства, които могат да ползваш с този абонамент.',
            u'Моля избери и изтрий устройство, за да продължиш да гледаш.'
            )
            devices = self.voyo.get_devices()
            dev_lst = []
            for name1, name2, act_text, dev_id in devices:
                dev_lst.append('{0} {1} {2} ({3})'.format(name1, name2, act_text, dev_id))
            i = dialog.select(u'Избери устройство за изтриване:', dev_lst)
            if not self.voyo.remove_device(devices[i][3]):
                dialog.ok(u'Грешка', u'Неуспешно изтриване на устройство.')

    def run(self, paramstring):
        params = dict(parse_qsl(paramstring))
        if params:
            if params['action'] == 'listing_sections':
                self.list_content(params)
            elif params['action'] == 'listing_tv':
                self.play_tv(params)
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
        else:
            self.list_categories()

if __name__ == '__main__':
    p = sys.argv[2][1:]
    v = voyo_plugin()
    v.run(p)

