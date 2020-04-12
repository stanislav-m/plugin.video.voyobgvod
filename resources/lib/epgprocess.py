import xml.etree.cElementTree as etree
import sys
import json
import requests
import gzip
import os
import time
import threading
import datetime
import codecs

epg_url = 'https://epg.kodibg.org/dl.php'
channel_names = ["bTVi", "bTV", "bTVComedy", "bTVCinema", "bTVAction", "bTVLady", "RING","VoyoCinema"]

class voyo_epg(threading.Thread):
    def __init__(self, workdir, url=epg_url, chan_set=channel_names):
        threading.Thread.__init__(self)
        self.__url = url
        self.__chan_set = chan_set
        self.__workdir = workdir
        if workdir[len(workdir)-1] != '/':
            self.__workdir += '/'
        self.__xmlepg = '{0}epg.xml'.format(self.__workdir)
        self.__gzfile = '{0}epg.xml.gz'.format(self.__workdir)

    def __download(self, chunk_size=128):
        requests.packages.urllib3.disable_warnings()
        attempt = 0
        while attempt < 5:
            attempt += 1
            try:
                r = requests.get(self.__url, stream=True, allow_redirects=True, verify=False)
                if r.status_code == 200:
                    with open(self.__gzfile, 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            fd.write(chunk)
                    return True
            except:
                return False
        return False

    def __unpack(self):
        with gzip.open(self.__gzfile, "rb") as f:
            try:
                content = f.read()
                with open(self.__xmlepg, 'wb') as xmlf:
                    xmlf.write(content)
                    return True
            except:
                return False

    def __getLogo(self):
        logos = {}
        chan =[]
        chan.extend(self.__chan_set)
        name = icon = ''
        for event, element in etree.iterparse(self.__xmlepg, events=("start", "end")):
            if len(chan) == 0:
                break
            if event == 'end':
                if element.tag == "channel":
                    ch = element.attrib['id']
                    if ch in chan:
                        logos[ch] = icon
                        del chan[ch.index(ch)]
                elif element.tag == 'display-name':
                    name = element.text
                elif element.tag == 'icon':
                    icon = element.attrib['src']
        return logos

    def __getChannelEpg(self):
        start = stop = title = desc = icon = ''
        epg_dict = {}
        emptylist = []
        for event, element in etree.iterparse(self.__xmlepg, events=("start", "end")):
            if event == 'end':
                if element.tag == "programme":
                    start = element.attrib['start']
                    stop = element.attrib['stop']
                    channel = element.attrib['channel']
                    if channel in self.__chan_set:
                        if not (channel in epg_dict):
                            epg_dict[channel] = []
                        #epg_dict[channel].append((start, stop, title, desc, icon))
                        epg_dict[channel].append((start, stop, title, '', icon))
                    start = stop = title = desc = icon = ''
                elif element.tag == 'title':
                    title = element.text
                elif element.tag == 'desc':
                    desc = element.text
                elif element.tag == 'icon':
                    icon = element.attrib['src']
        return epg_dict

    def __tidyup(self):
        if os.path.exists(self.__xmlepg):
            os.unlink(self.__xmlepg)
        if os.path.exists(self.__gzfile):
            os.unlink(self.__gzfile)

    def run(self):
        epg_exists = False
        epgfname = '{0}epg.json'.format(self.__workdir)
        logofname = '{0}logos.json'.format(self.__workdir)
        if os.path.exists(epgfname):
            mtime = os.path.getmtime(epgfname)
            now = time.time()
            epg_exists = True
        if not epg_exists or mtime + 24*60*60 < now: # more that 24 hours - expired
            if self.__download() and self.__unpack():
                logostr = json.dumps(self.__getLogo(), ensure_ascii=False)
                with open(logofname, 'w') as f:
                    f.write(logostr)
                epg_str = json.dumps(self.__getChannelEpg(), ensure_ascii=False)
                with codecs.open(epgfname, 'w', 'utf-8') as f:
                    f.write(epg_str)
            self.__tidyup()

def main():
    epg = voyo_epg('./')
    epg.start()
    epg.join()
    if os.path.exists('epg.json'):
        with codecs.open('epg.json', 'r', 'utf-8') as f:
            epgs = f.read()
            epgd = json.loads(epgs)
            for e in epgd:
                print('\n==> {0}\n'.format(e))
                eepglst = epgd[e]
                for it in eepglst:
                    print('{0} - {1} {2}'.format(
                        it[0], it[1], it[2].encode('utf-8')))


if __name__ == '__main__':
    main()

