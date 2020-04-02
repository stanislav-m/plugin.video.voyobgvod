# -*- coding: utf-8 -*-
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import sys

def Log(msg, level=xbmc.LOGDEBUG):
    __addon__ = xbmcaddon.Addon()
    xbmc.log("{0} v{1} | {2}".format(
        __addon__.getAddonInfo('id'),
        __addon__.getAddonInfo('version'),
        msg), level)

def jsonRPC(method, props='', param=None):
    """ Wrapper for Kodi's executeJSONRPC API """
    rpc = {'jsonrpc': '2.0',
           'method': method,
           'params': {},
           'id': 1}

    if props:
        rpc['params']['properties'] = props.split(',')
    if param:
        rpc['params'].update(param)
        if 'playerid' in param.keys():
            res_pid = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Player.GetActivePlayers","id": 1}')
            pid = [i['playerid'] for i in json.loads(res_pid)['result'] if i['type'] == 'video']
            pid = pid[0] if pid else 0
            rpc['params']['playerid'] = pid

    res = json.loads(xbmc.executeJSONRPC(json.dumps(rpc)))
    if 'error' in res.keys():
        Log(res['error'])
        return res['error']

    result = res['result']
    return result if type(result) == unicode else res['result'].get(props, res['result'])


def sleep(sec):
    if xbmc.Monitor().waitForAbort(sec):
        Log('Abort requested - exiting addon')
        sys.exit()

