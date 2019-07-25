# -*- coding: utf-8 -*-
import sys
from urllib import urlencode
from urllib import quote_plus
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
from bs4 import BeautifulSoup
from resources.lib.voyo_web_api import *
import inputstreamhelper
import uuid

config_par = ['username', 'password', 'device']
settings = {}

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


def getSettings():
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

voyo = voyobg()

_url = sys.argv[0]
_handle = int(sys.argv[1])
__addon__   = xbmcaddon.Addon()

getSettings()
while not voyo.login():
    dialog = xbmcgui.Dialog()
    dialog.ok(u'Грешка', u'Некоректни данни за абонамент!')
    __addon__.openSettings()
    getSettings()


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
    if xbmc.getCondVisibility('System.Platform.{}'.format(platform)):
      return platform
  return "Unknown"


def log_primitive(msg, level):
    if str(type(msg)) == "<type 'unicode'>":
        s = msg.encode('utf-8')
    else:
        s = str(msg)
    xbmc.log("{} v{} | {}".format(get_addon_id(), get_addon_version(), s), level)

def log(msg, level=xbmc.LOGDEBUG):
    try:
        level = xbmc.LOGNOTICE
        if str(type(msg)) == "<type 'list'>" or str(type(msg)) == "<type 'tuple'>":
            for m in msg:
                log_primitive(msg, level)
        elif str(type(msg)) == "<type 'dict'>":
            for key in msg:
                log_primitive('{} : {}'.format(key, msg[key]), level)
        else:
            log_primitive(msg, level)

    except:
        try:
            import traceback
            er = traceback.format_exc(sys.exc_info())
            xbmc.log('%s | Logging failure: %s' % (get_addon_id(), er), level)
        except:
            pass


def list_categories():
    xbmcplugin.setPluginCategory(_handle, 'Voyobg')
    xbmcplugin.setContent(_handle, 'videos')
    categories = voyo.sections()
    for name, link in categories:
        li = xbmcgui.ListItem(label=name)
        li.setInfo('video', {'title': name,
                                    'genre': 'Voyo content',
                                    'mediatype': 'video'})
        url = get_url(action='listing_sections', category=link.replace('/', '_'))
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def list_item(name, link, img, plot, act_str, playable):
    log('{} :  {} - {}'.format(name, link, img))
    li = xbmcgui.ListItem(label=name)
    li.setArt({'thumb': img, 'icon': '', 'fanart': ''})
    li.setInfo('video', {'title': name, 'Plot': plot})
    if playable:
        url = link
    else:
        url = get_url(action=act_str, category=link.replace('/', '_'),
                      name=name, img=img, plot=plot, link=link)
    if playable:
        li.setProperty("IsPlayable", str(True))
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, li)
    else:
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)

def list_content(category):
    cat_link = category.replace('_', '/')
    xbmcplugin.setPluginCategory(_handle, category)
    xbmcplugin.setContent(_handle, 'videos')
    if cat_link == '/tv-radio/':
        content = voyo.tv_radio(cat_link)
        action_str = 'play_tv'
        for cont in content:
            name, link, img = cont
            list_item(name, link, img, '', action_str, False)
    else:
        content = voyo.process_page(cat_link)
        if str(type(content)) == "<type 'list'>":
            action_str = 'listing_sections'
            for cont in content:
                name, link, img = cont
                list_item(name, link, img, '', action_str, False)
        else:
            action_str = 'play_vod'
            name, link, img, plot = content
            list_item(name, link, img, plot, action_str, False)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def device_status():
    dialog = xbmcgui.Dialog()
    while not voyo.check_device():
        dialog.ok(
        u'Грешка', 
        u'Достигнал си максималния брой устройства, които могат да ползваш с този абонамент.',
        u'Моля избери и изтрий устройство, за да продължиш да гледаш.'
        )
        devices = voyo.get_devices()
        dev_lst = []
        for name1, name2, act_text, dev_id in devices:
            dev_lst.append('{} {} {} ({})'.format(name1, name2, act_text, dev_id))
        i = dialog.select(u'Избери устройство за изтриване:', dev_lst)
        if not voyo.remove_device(devices[i][3]):
            dialog.ok(u'Грешка', u'Неуспешно изтриване на устройство.')


def play_tv(category, name, link, img, plot):
    device_status()
    play_url = voyo.channel(link)
    if play_url:
        headers = "User-agent: stagefright/1.2 (Linux;Android 6.0)"
        PROTOCOL = 'hls'
        is_helper = inputstreamhelper.Helper(PROTOCOL)
        if is_helper.check_inputstream():
            li = xbmcgui.ListItem(label=name, path=play_url)
            li.setInfo(type="Video", infoLabels={"Title":name, "Plot":plot})
            li.setArt({'thumb':img, 'icon':'', 'fanart':''})
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            li.setProperty('inputstream.adaptive.stream_headers', headers)
            li.setProperty("IsPlayable", str(True))
            xbmc.Player().play(item=play_url, listitem=li)
        else:
            log('inputstreamhelper check failed.')


def play_vod(category, name, link, img, plot):
    device_status()
    play_param = voyo.process_play_url(link)
    if play_param:
        headers = "User-agent: stagefright/1.2 (Linux;Android 6.0)"
        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'
        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():
            li = xbmcgui.ListItem(label='Play( {} )'.format(name), path=play_param['play_url'])
            li.setInfo(type="Video", infoLabels={"Title":name, "Plot":plot})
            li.setArt({'thumb':img, 'icon':'', 'fanart':''})
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            li.setProperty('inputstream.adaptive.stream_headers', headers)
            li.setProperty('inputstream.adaptive.license_type', DRM)
            licURL = play_param['license_url'] + '||R{SSM}|BJBwvlic'
            li.setProperty('inputstream.adaptive.license_key', licURL)
            li.setMimeType('application/dash+xml')
            li.setProperty("IsPlayable", str(True))
            xbmc.Player().play(item=play_param['play_url'], listitem=li)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'listing_sections':
            list_content(params['category'])
        elif params['action'] == 'play_vod':
            play_vod(params['category'], params['name'], params['link'],
                    params['img'], params['plot'])
        elif params['action'] == 'play_tv':
            play_tv(params['category'], params['name'], params['link'],
                    params['img'], '') #params['plot'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
