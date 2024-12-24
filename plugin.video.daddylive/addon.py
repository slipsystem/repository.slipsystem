# -*- coding: utf-8 -*-
'''
***********************************************************
*
* @file addon.py
* @package script.module.thecrew
*
* Created on 2024-03-08.
* Copyright 2024 by The Crew. All rights reserved.
*
* @license GNU General Public License, version 3 (GPL-3.0)
*
********************************************************cm*
'''
# pylint: disable-msg=F0401

import re
import os
import sys
import json
import html
from urllib.parse import urlencode, quote, unquote, parse_qsl, quote_plus, urlparse
from datetime import datetime, timedelta, timezone
import time
import requests
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
import os



def create_directory(dir_path, dir_name=None):
    if dir_name:
        dir_path = os.path.join(dir_path, dir_name)
    dir_path = dir_path.strip()
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.daddylive')
DATA_PATH = os.path.join(xbmcvfs.translatePath('special://home/addons/plugin.video.daddylive'), 'resources')

def tv_icons():
    return create_directory(DATA_PATH, "tv_icons")

tv_icons_dir = tv_icons()
mode = addon.getSetting('mode')
baseurl = 'https://dlhd.so/'
json_url = f'{baseurl}stream/stream-%s.php'
schedule_url = baseurl + 'schedule/schedule-generated.json'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'
FANART = addon.getAddonInfo('fanart')
ICON = addon.getAddonInfo('icon')



def log(msg):
    LOGPATH = xbmcvfs.translatePath('special://logpath/')
    FILENAME = 'daddylive.log'
    LOG_FILE = os.path.join(LOGPATH, FILENAME)
    try:
        if isinstance(msg, str):
                _msg = f'\n    {msg}'

        else:
            raise TypeError('log() msg not of type str!')

        if not os.path.exists(LOG_FILE):
            f = open(LOG_FILE, 'w', encoding='utf-8')
            f.close()
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            line = ('[{} {}]: {}').format(datetime.now().date(), str(datetime.now().time())[:8], _msg)
            f.write(line.rstrip('\r\n') + '\n')
    except (TypeError, Exception) as e:
        try:
            xbmc.log(f'[ Daddylive ] Logging Failure: {e}', 2)
        except:
            pass



def get_local_time(utc_time_str):
    try:
        event_time_utc = datetime.strptime(utc_time_str, '%H:%M')
    except TypeError:
        event_time_utc = datetime(*(time.strptime(utc_time_str, '%H:%M')[0:6]))
    timezone_offset_minutes = -300
    event_time_local = event_time_utc + timedelta(minutes=timezone_offset_minutes)
    local_time_str = event_time_local.strftime('%I:%M %p').lstrip('0')
    return local_time_str


def build_url(query):
    return addon_url + '?' + urlencode(query)


def addDir(title, dir_url, is_folder=True):
    li = xbmcgui.ListItem(title)
    icon_path = os.path.join(tv_icons_dir, title + '.png')
    if os.path.exists(icon_path):
        iconpath = icon_path
    else:
        iconpath = ICON
    labels = {'title': title, 'plot': title, 'mediatype': 'video'}
    kodiversion = getKodiversion()
    if kodiversion < 20:
        li.setInfo("video", labels)
    else:
        infotag = li.getVideoInfoTag()
        infotag.setMediaType(labels.get("mediatype", "video"))
        infotag.setTitle(labels.get("title", "Daddylive"))
        infotag.setPlot(labels.get("plot", labels.get("title", "Daddylive")))
    li.setArt({'thumb': '', 'poster': '', 'banner': '', 'icon': iconpath, 'fanart': FANART})
    if is_folder is True:
        li.setProperty("IsPlayable", 'false')
    else:
        li.setProperty("IsPlayable", 'true')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=dir_url, listitem=li, isFolder=is_folder)


def closeDir():
    xbmcplugin.endOfDirectory(addon_handle)


def getKodiversion():
    return int(xbmc.getInfoLabel("System.BuildVersion")[:2])


def Main_Menu():
    menu = [
        ['Sports Guide', 'sched'],
        ['LIVE TV', 'live_tv'],
        ['Kids Channels', 'kids_tv'],
        ['Sports Channels', 'sports_tv'],
        ['Crime Channels', 'crime_tv'],
        ['USA Channels', 'usa_tv'],
        ['UK Channels', 'uk_tv'],
        ['My Channels', 'fav_tv'],
    ]
    for m in menu:
        addDir(m[0], build_url({'mode': 'menu', 'serv_type': m[1]}))
    closeDir()


def getCategTrans():
    hea = {'User-Agent': UA}
    categs = []

    try:
        schedule = requests.get(schedule_url, headers=hea, timeout=10).json()
        for date_key, events in schedule.items():
            for categ, events_list in events.items():
                categs.append((categ, json.dumps(events_list)))
    except Exception as e:
        xbmcgui.Dialog().ok("Error", f"Error fetching category data: {e}")
        return []

    return categs


def Menu_Trans():
    categs = getCategTrans()
    if not categs:
        return

    for categ_name, events_list in categs:
        addDir(categ_name, build_url({'mode': 'showChannels', 'trType': categ_name}))
    closeDir()


def ShowChannels(categ, channels_list):
    for item in channels_list:
        title = item.get('title')
        addDir(title, build_url({'mode': 'trList', 'trType': categ, 'channels': json.dumps(item.get('channels'))}), True)
    closeDir()


def getTransData(categ):
    trns = []
    categs = getCategTrans()

    for categ_name, events_list_json in categs:
        if categ_name == categ:
            events_list = json.loads(events_list_json)
            for item in events_list:
                event = item.get('event')
                time_str = item.get('time')
                event_time_local = get_local_time(time_str)
                title = f'{event_time_local} {event}'
                channels = item.get('channels')
                trns.append({
                    'title': title,
                    'channels': [{'channel_name': channel.get('channel_name'), 'channel_id': channel.get('channel_id')} for channel in channels]
                })

    return trns


def TransList(categ, channels):
    for channel in channels:
        channel_title = html.unescape(channel.get('channel_name'))
        channel_id = channel.get('channel_id')
        addDir(channel_title, build_url({'mode': 'trLinks', 'trData': json.dumps({'channels': [{'channel_name': channel_title, 'channel_id': channel_id}]})}), False)
    closeDir()


def getSource(trData):
    data = json.loads(unquote(trData))

    channels_data = data.get('channels')

    if channels_data is not None and isinstance(channels_data, list):
        url_stream = f'{baseurl}stream/stream-{channels_data[0]["channel_id"]}.php'
        xbmcplugin.setContent(addon_handle, 'videos')
        PlayStream(url_stream)


def list_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()

def kids_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        item_list = ['Boomerang', 'Cartoon Network', 'Disney', 'Disney Channel', 'Disney XD', 'Disney JR', 'Nick JR', 'Nick', 'Nick Music', 'Nicktoons', 'Universal Kids USA', 'Sky Cinema Family UK']
        if c[1] in item_list:
            addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()

def sports_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        item_list = ['Super Sport', 'Sky Sports', 'Sky Sports Football UK' , 'Sky Sports Arena UK' , 'Sky Sports Action UK' , 'Sky Sports Main Event' , 'Sky sports Premier League' , 'Sky Sports F1 UK' , 'Sky Sports F1 DE' , 'Sky Sports Cricket' , 'Sky Sports Golf UK' , 'Sky Sports Golf Italy' , 'Sky Sport MotoGP Italy' , 'Sky Sport Tennis Italy' , 'Sky Sports Tennis UK' , 'Sky Sports Tennis DE' , 'Sky Sport F1 Italy' , 'Sky Sports News UK' , 'Sky Sports MIX UK' , 'Sky Sport Top Event DE' , 'Sky Sport Mix DE' , 'Sky Sport Bundesliga 1 HD' , 'Sky Sport Austria 1 HD' , 'SportsNet New York (SNY)' , 'Sky Sport Football Italy' , 'Sky Sport UNO Italy' , 'Sky Sport Arena Italy' , 'Sky Sports Racing UK' , 'Sky Sport 1 NZ' , 'Sky Sport 2 NZ' , 'Sky Sport 3 NZ' , 'Sky Sport 4 NZ' , 'Sky Sport 5 NZ' , 'Sky Sport 6 NZ' , 'Sky Sport 7 NZ' , 'Sky Sport 8 NZ' , 'Sky Sport 9 NZ' , 'Sky Sport Select NZ' , 'Sportsnet Ontario' , 'Sportsnet One' , 'Sportsnet West' , 'Sportsnet East' , 'Sportsnet 360' , 'Sportsnet World' , 'SuperSport Grandstand' , 'SuperSport PSL' , 'SuperSport Premier league' , 'SuperSport LaLiga' , 'SuperSport Variety 1' , 'SuperSport Variety 2' , 'SuperSport Variety 3' , 'SuperSport Variety 4' , 'SuperSport Action' , 'SuperSport Rugby' , 'SuperSport Golf' , 'SuperSport Tennis' , 'SuperSport Motorsport' , 'Supersport Football' , 'SuperSport Cricket' , 'SuperSport MaXimo 1' , 'TNT Sports 1 UK' , 'TNT Sports 2 UK' , 'TNT Sports 3 UK' , 'TNT Sports 4 UK' , 'TF1 France' , 'TSN1' , 'TSN2' , 'TSN3' , 'TSN4' , 'TSN5' , 'Rally Tv' , 'NBA TV USA' , 'NBC Sports Chicago' , 'NBC Sports Philadelphia' , 'NBC Sports Washington' , 'Fox Sports 1 USA' , 'Fox Sports 2 USA' , 'FOX Soccer Plus' , 'Fox Cricket' , 'FOX Sports 502 AU' , 'FOX Sports 503 AU' , 'FOX Sports 504 AU' , 'FOX Sports 505 AU' , 'FOX Sports 506 AU' , 'FOX Sports 507 AU' , 'ESPN USA' , 'ESPN2 USA' , 'ESPNU USA' , 'BeIN SPORTS USA' , 'beIN SPORTS en Español' , 'beIN SPORTS Australia 1' , 'beIN SPORTS Australia 2' , 'beIN SPORTS Australia 3' , 'beIN Sports MENA English 1' , 'beIN Sports MENA English 2' , 'beIN Sports MENA English 3' , 'beIN Sports MENA 1' , 'beIN Sports MENA 2' , 'beIN Sports MENA 3' , 'beIN Sports MENA 4' , 'beIN Sports MENA 5' , 'beIN Sports MENA 6' , 'beIN Sports MENA 7' , 'beIN Sports MENA 8' , 'beIN Sports MENA 9' , 'beIN SPORTS XTRA 1' , 'beIN SPORTS XTRA 2']
        if c[1] in item_list:
            addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()

def fav_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        item_list = ['Comedy Central', 'A&E USA']
        if c[1] in item_list:
            addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()

def crime_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        item_list = ['Crime+ Investigation USA', 'Sky Crime', 'Oxygen True Crime']
        if c[1] in item_list:
            addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()    

def uk_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        item_list = ['BBC One UK' , 'BBC Two UK' , 'BBC Three UK' , 'BBC Four UK' , 'Channel 4 UK' , 'Channel 5 UK' , 'DAZN 1 UK' , 'EuroSport 1 UK' , 'EuroSport 2 UK' , 'Film4 UK' , 'Gold UK' , 'ITV 1 UK' , 'ITV 2 UK' , 'ITV 3 UK' , 'ITV 4 UK' , 'LaLigaTV UK' , 'MTV UK' , 'MUTV UK' , 'Racing Tv UK' , 'Sky Sports Football UK' , 'Sky Sports Arena UK' , 'Sky Sports Action UK' , 'Sky Sports F1 UK' , 'Sky Sports Golf UK' , 'Sky Sports Tennis UK' , 'Sky Sports News UK' , 'Sky Sports MIX UK' , 'Sky Sports Racing UK' , 'S4C UK' , 'Sky Cinema Premiere UK' , 'Sky Cinema Select UK' , 'Sky Cinema Hits UK' , 'Sky Cinema Greats UK' , 'Sky Cinema Animation UK' , 'Sky Cinema Family UK' , 'Sky Cinema Action UK' , 'Sky Cinema Comedy UK' , 'Sky Cinema Thriller UK' , 'Sky Cinema Drama UK' , 'Sky Cinema Sci-Fi Horror UK' , 'Sky Showcase UK' , 'Sky Arts UK' , 'Sky Comedy UK' , 'TNT Sports 1 UK' , 'TNT Sports 2 UK' , 'TNT Sports 3 UK' , 'TNT Sports 4 UK' , 'Viaplay Sports 1 UK' , 'Viaplay Sports 2 UK' , 'Viaplay Xtra UK']
        if c[1] in item_list:
            addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()

def usa_gen():
    addon_url = baseurl
    chData = channels()
    for c in chData:
        item_list = ['ABC USA' , 'A&E USA' , 'AMC USA' , 'ACC Network USA' , 'Adult Swim' , 'BET USA' , 'Bravo USA' , 'BIG TEN Network (BTN USA)' , 'COZI TV USA' , 'CMT USA' , 'CBS USA' , 'CW USA' , 'CW PIX 11 USA' , 'CNBC USA' , 'CNN USA' , 'Cinemax USA' , 'Crime+ Investigation USA' , 'Comet USA' , 'Cooking Channel USA' , 'CBSNY USA' , 'Court TV USA' , 'ESPN USA' , 'ESPN2 USA' , 'ESPNU USA' , 'Fox Sports 1 USA' , 'Fox Sports 2 USA' , 'FOX Deportes USA' , 'FOX USA' , 'FX USA' , 'FXX USA' , 'FOXNY USA' , 'FUSE TV USA' , 'GOLF Channel USA' , 'Galavisión USA' , 'HBO USA' , 'HBO2 USA' , 'HBO Comedy USA' , 'HBO Family USA' , 'HBO Latino USA' , 'HBO Signature USA' , 'HBO Zone USA' , 'History USA' , 'Investigation Discovery (ID USA)' , 'ION USA' , 'IFC TV USA' , 'Longhorn Network USA' , 'MSG USA' , 'MTV USA' , 'MAVTV USA' , 'MGM+ USA / Epix' , 'MLB Network USA' , 'MASN USA' , 'MY9TV USA' , 'METV USA' , 'NHL Network USA' , 'NESN USA' , 'NBC USA' , 'NBA TV USA' , 'NBCNY USA' , 'NewsNation USA' , 'Newsmax USA' , 'Nat Geo Wild USA' , 'Pac-12 Network USA' , 'POP TV USA' , 'PBS USA USA' , 'SEC Network USA' , 'Showtime USA' , 'Showtime SHOxBET USA' , 'Showtime 2 USA (SHO2) USA' , 'Showtime Showcase USA' , 'Showtime Extreme USA' , 'Showtime Family Zone (SHO Family Zone) USA' , 'Showtime Next (SHO Next) USA' , 'Showtime Women USA' , 'SYFY USA' , 'TUDN USA' , 'TBS USA' , 'TNT USA' , 'TruTV USA' , 'TCM USA' , 'TMC Channel USA' , 'TV ONE USA' , 'USA Network' , 'Universal Kids USA' , 'VH1 USA' , 'WETV USA' , 'YES Network USA' , '5 USA']
        if c[1] in item_list:
            addDir(c[1], build_url({'mode': 'play', 'url': addon_url + c[0]}), False)
    closeDir()

def channels():
    url = baseurl + '/24-7-channels.php'
    do_adult = xbmcaddon.Addon().getSetting('adult_pw')

    hea = {
        'Referer': baseurl + '/',
        'user-agent': UA,
    }

    resp = requests.post(url, headers=hea).text
    ch_block = re.compile('<center><h1(.+?)tab-2', re.MULTILINE | re.DOTALL).findall(str(resp))
    chan_data = re.compile('href=\"(.*)\" target(.*)<strong>(.*)</strong>').findall(ch_block[0])

    channels = []
    for c in chan_data:
        if not "18+" in c[2]:
            channels.append([c[0], c[2]])
        if do_adult == 'lol' and "18+" in c[2]:
            channels.append([c[0], c[2]])

    return channels


def PlayStream(link):
    url = link

    hea = {
        'Referer': baseurl + '/',
        'user-agent': UA,
    }

    resp = requests.post(url, headers=hea).text
    url_1 = re.findall('iframe src="(.*?)"', resp)[0]

    hea = {
        'Referer': url,
        'user-agent': UA,
    }

    resp2 = requests.get(url_1, headers=hea, timeout=10)
    links = re.findall('source: \'([^\']*)', resp2.text)
    if links:
        link = str(links[0])

        parsed_url = urlparse(url_1)
        referer_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
        referer = quote_plus(referer_base)
        user_agent = quote_plus(UA)

        link = f'{link}|Referer={referer}/&Origin={referer}&Keep-Alive=true&User-Agent={user_agent}'

        liz = xbmcgui.ListItem('Daddylive', path=link)
        liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
        liz.setMimeType('application/x-mpegURL')
        liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
        liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
        liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
        xbmcplugin.setResolvedUrl(addon_handle, True, liz)


kodiversion = getKodiversion()
mode = params.get('mode', None)

if not mode:
    Main_Menu()
else:
    if mode == 'menu':
        servType = params.get('serv_type')
        if servType == 'sched':
            Menu_Trans()
        if servType == 'live_tv':
            list_gen()
        if servType == 'kids_tv':
            kids_gen()
        if servType == 'fav_tv':
            fav_gen()
        if servType == 'sports_tv':
            sports_gen()
        if servType == 'usa_tv':
            usa_gen()
        if servType == 'uk_tv':
            uk_gen()
        if servType == 'crime_tv':
            crime_gen()

    if mode == 'showChannels':
        transType = params.get('trType')
        channels = getTransData(transType)
        ShowChannels(transType, channels)

    if mode == 'trList':
        transType = params.get('trType')
        channels = json.loads(params.get('channels'))
        TransList(transType, channels)

    if mode == 'trLinks':
        trData = params.get('trData')
        getSource(trData)

    if mode == 'play':
        link = params.get('url')
        PlayStream(link)
