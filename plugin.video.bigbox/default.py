import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import os
import subprocess
import time
import shutil
import stat
import xbmc
import xbmcaddon
import re
import sqlite3
import ConfigParser
import xml.etree.ElementTree as ET
from os import listdir
from os.path import isfile, join
	
addon = xbmcaddon.Addon(id='plugin.video.bigbox')
addonPath = addon.getAddonInfo('path')
addonIcon = addon.getAddonInfo('icon')
addonVersion = addon.getAddonInfo('version')
dialog = xbmcgui.Dialog()
language = addon.getLocalizedString
scriptid = 'plugin.video.bigbox'
addon_id = 'plugin.video.bigbox'
fanart = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id , 'fanart.jpg'))
icon = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'icon.png'))

DIALOG = xbmcgui.Dialog()

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')


steamLinux = addon.getSetting("SteamWin").decode("utf-8")
kodiLinux = addon.getSetting("KodiLinux").decode("utf-8")
steamWin = addon.getSetting("SteamWin").decode("utf-8")
kodiWin = addon.getSetting("KodiWin").decode("utf-8")
steamOsx = addon.getSetting("SteamOsx").decode("utf-8")
kodiOsx = addon.getSetting("KodiOsx").decode("utf-8")
delUserScriptSett = addon.getSetting("DelUserScript")
quitKodiSetting = addon.getSetting("QuitKodi")
busyDialogTime = int(addon.getSetting("BusyDialogTime"))
scriptUpdateCheck = addon.getSetting("ScriptUpdateCheck")
filePathCheck = addon.getSetting("FilePathCheck")
kodiPortable = addon.getSetting("KodiPortable")
preScriptEnabled = addon.getSetting("PreScriptEnabled")
preScript = addon.getSetting("PreScript").decode("utf-8")
postScriptEnabled = addon.getSetting("PostScriptEnabled")
NoArtworkEnabled = addon.getSetting("NoArtworkEnabled")
CheckRomExists = addon.getSetting("CheckExists")
UpdateEnabled = addon.getSetting("UpdateEnabled")
postScript = addon.getSetting("PostScript").decode("utf-8")
osWin = xbmc.getCondVisibility('system.platform.windows')
osOsx = xbmc.getCondVisibility('system.platform.osx')
osLinux = xbmc.getCondVisibility('system.platform.linux')
osAndroid = xbmc.getCondVisibility('system.platform.android')
wmctrlCheck = addon.getSetting("WmctrlCheck")
suspendAudio = addon.getSetting("SuspendAudio")

#HACK: sys.getfilesystemencoding() is not supported on all systems (e.g. Android)
txt_encode = 'utf-8'
try:
	txt_encode = sys.getfilesystemencoding()
except:
	pass
#osAndroid returns linux + android
if osAndroid: 
	osLinux = 0
	txt_encode = 'utf-8'

def log(msg):
	msg = msg.encode(txt_encode)
	xbmc.log('%s: %s' % (scriptid, msg))


def getAddonInstallPath():
	path = addon.getAddonInfo('path').decode("utf-8")
	return path


def getAddonDataPath():
	path = xbmc.translatePath('special://profile/addon_data/%s' % scriptid).decode("utf-8")
	if not os.path.exists(path):
		log('addon userdata folder does not exist, creating: %s' % path)
		try:
			os.makedirs(path)
			log('created directory: %s' % path)
		except:
			log('ERROR: failed to create directory: %s' % path)
			dialog.notification(language(50123), language(50126), addonIcon, 5000)
	return path


def copyLauncherScriptsToUserdata():
	oldBasePath = os.path.join(getAddonInstallPath(), 'resources', 'scripts')
	newBasePath = os.path.join(getAddonDataPath(), 'scripts')
	if osWin:
		oldPath = os.path.join(oldBasePath, 'SteamLauncher-AHK.ahk')
		newPath = os.path.join(newBasePath, 'SteamLauncher-AHK.ahk')
		copyFile(oldPath, newPath)
		oldPath = os.path.join(oldBasePath, 'BigBoxLauncher-AHK.exe')
		newPath = os.path.join(newBasePath, 'BigBoxLauncher-AHK.exe')
		copyFile(oldPath, newPath)
	elif osLinux + osOsx:
		oldPath = os.path.join(oldBasePath, 'steam-launch.sh')
		newPath = os.path.join(newBasePath, 'steam-launch.sh')
		copyFile(oldPath, newPath)


def copyFile(oldPath, newPath):
	newDir = os.path.dirname(newPath)
	if not os.path.isdir(newDir):
		log('userdata scripts folder does not exist, creating: %s' % newDir)
		try:
			os.mkdir(newDir)
			log('sucsessfully created userdata scripts folder: %s' % newDir)
		except:
			log('ERROR: failed to create userdata scripts folder: %s' % newDir)
			dialog.notification(language(50123), language(50126), addonIcon, 5000)
	if not os.path.isfile(newPath):
		log('script file does not exist, copying to userdata: %s' % newPath)
		try:
			shutil.copy2(oldPath, newPath)
			log('sucsessfully copied userdata script: %s' % newPath)
		except:
			log('ERROR: failed to copy script file to userdata: %s' % newPath)
			dialog.notification(language(50123), language(50126), addonIcon, 5000)
	else:
		log('script file already exists, skipping copy to userdata: %s' % newPath)


def makeScriptExec():
	scriptPath = os.path.join(getAddonDataPath(), 'scripts', 'steam-launch.sh')
	if os.path.isfile(scriptPath):
		if not stat.S_IXUSR & os.stat(scriptPath)[stat.ST_MODE]:
			log('steam-launch.sh not executable: %s' % scriptPath)
			try:
				os.chmod(scriptPath, stat.S_IRWXU)
				log('steam-launch.sh now executable: %s' % scriptPath)
			except:
				log('ERROR: unable to make steam-launch.sh executable, exiting: %s' % scriptPath)
				dialog.notification(language(50123), language(50126), addonIcon, 5000)
			log('steam-launch.sh executable: %s' % scriptPath)


def usrScriptDelete():
	if delUserScriptSett == 'true':
		log('deleting userdata scripts, option enabled: delUserScriptSett = %s' % delUserScriptSett)
		scriptFile = os.path.join(getAddonDataPath(), 'scripts', 'SteamLauncher-AHK.ahk')
		delUserScript(scriptFile)
		scriptFile = os.path.join(getAddonDataPath(), 'scripts', 'BigBoxLauncher-AHK.exe')
		delUserScript(scriptFile)
		scriptFile = os.path.join(getAddonDataPath(), 'scripts', 'steam-launch.sh')
		delUserScript(scriptFile)
	elif delUserScriptSett == 'false':
		log('skipping deleting userdata scripts, option disabled: delUserScriptSett = %s' % delUserScriptSett)


def delUserScript(scriptFile):
	if os.path.isfile(scriptFile):
		try:
			os.remove(scriptFile)
			log('found and deleting: %s' % scriptFile)
		except:
			log('ERROR: deleting failed: %s' % scriptFile)
			dialog.notification(language(50123), language(50126), addonIcon, 5000)
		addon.setSetting(id="DelUserScript", value="false")


def fileChecker():
	if osLinux:
		if wmctrlCheck == 'true':
			if subprocess.call(["which", "wmctrl"]) != 0:
				log('ERROR: System program "wmctrl" not present, install it via you system package manager or if you are running the SteamOS compositor disable the addon option "Check for program wmctrl" (ONLY FOR CERTAIN USE CASES!!)')
				dialog.notification(language(50123), language(50126), addonIcon, 5000)
			else:
				log('wmctrl present, checking if a window manager is running...')
				if subprocess.call('DISPLAY=:0 wmctrl -l', shell=True) != 0:
					log('ERROR: A window manager is NOT running - unless you are using the SteamOS compositor Steam BPM needs a windows manager. If you are using the SteamOS compositor disable the addon option "Check for program wmctrl"')
					dialog.notification(language(50123), language(50126), addonIcon, 5000)
				else:
					log('A window manager is running...')
	if filePathCheck == 'true':
		log('running program file check, option is enabled: filePathCheck = %s' % filePathCheck)
		if osWin:
			steamWin = addon.getSetting("SteamWin")
			kodiWin = addon.getSetting("KodiWin")
			steamExe = os.path.join(steamWin).decode("utf-8")
			xbmcExe = os.path.join(kodiWin).decode("utf-8")
			programFileCheck(steamExe, xbmcExe)
		elif osOsx:
			steamOsx = addon.getSetting("SteamOsx")
			kodiOsx = addon.getSetting("KodiOsx")
			steamExe = os.path.join(steamOsx).decode("utf-8")
			xbmcExe = os.path.join(kodiOsx).decode("utf-8")
			programFileCheck(steamExe, xbmcExe)
		elif osLinux:
			steamLinux = addon.getSetting("SteamLinux")
			kodiLinux = addon.getSetting("KodiLinux")
			steamExe = os.path.join(steamLinux).decode("utf-8")
			xbmcExe = os.path.join(kodiLinux).decode("utf-8")
			programFileCheck(steamExe, xbmcExe)
	else:
		log('skipping program file check, option disabled: filePathCheck = %s' % filePathCheck)


def fileCheckDialog(programExe):
	log('ERROR: dialog to go to addon settings because executable does not exist: %s' % programExe)
	if dialog.yesno(language(50123), programExe, language(50122), language(50121)):
		log('yes selected, opening addon settings')
		addon.openSettings()
		fileChecker()
	else:
		log('ERROR: no selected with invalid executable, exiting: %s' % programExe)


def programFileCheck(steamExe, xbmcExe):
	if osWin + osLinux:
		if os.path.isfile(os.path.join(steamExe)):
			log('Steam executable existis %s' % steamExe)
		else:
			fileCheckDialog(steamExe)
		if os.path.isfile(os.path.join(xbmcExe)):
			log('Xbmc executable existis %s' % xbmcExe)
		else:	
			fileCheckDialog(xbmcExe)
		DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
		conn = sqlite3.connect(DatabasePath)
		date = ''
		datemodded = ''
		c = conn.cursor()
		try:
			c.execute('''ALTER TABLE games ADD COLUMN
				Banner text''')
		except:
			nothing = ''
			
		try:
			c.execute('''ALTER TABLE platforms ADD COLUMN
				Banner text''')
		except:
			nothing = ''
			
		try:
			c.execute('''ALTER TABLE games ADD COLUMN
				Logo text''')
		except:
			nothing = ''
			
			
		try:
			c.execute('''ALTER TABLE platforms ADD COLUMN
				Logo text''')
		except:
			nothing = ''
			
		try:
			c.execute('''ALTER TABLE games ADD COLUMN
				Videos text''')
		except:
			nothing = ''
			
		try:
			c.execute('''CREATE TABLE games
				(Title text, ApplicationPath text, Platform text, Emulator text,LastPlayedDate text,DateAdded text,Notes text, ReleaseDate text, Icon text, Fanart text, Completed text, Favorite text, Rating text, Genre text, Banner text, Logo text, Videos text)''')
		except:
			nothing = "nothing"
		try:
			c.execute('''CREATE TABLE platforms
				(Title text, Description text, Icon text, Fanart text,Banner text,Logo text)''')
		except:
			nothing = "nothing"
			
		try:
			c.execute('''CREATE TABLE emulatorcommands
				(Emulator text, Platform text, CommandLine text)''')
		except:
			nothing = "nothing"
		
		try:
			c.execute('''CREATE TABLE updatelog
				(Platform text, LastUpdate text)''')
		except:
			nothing = "nothing"
		
		try:
			c.execute('''CREATE TABLE emulators
				(Emulator text, ApplicationPath text, CommandLine text)''')
		except:
			nothing = "nothing"
		
		try:
			c.execute('''CREATE TABLE removedplatforms
				(Platform text)''')
		except:
			nothing = "nothing"

		if UpdateEnabled == 'true':
			UpdateCheck()
				
	if osOsx:
		if os.path.isdir(os.path.join(steamExe)):
			log('Steam folder existis %s' % steamExe)
		else:
			fileCheckDialog(steamExe)
		if os.path.isdir(os.path.join(xbmcExe)):
			log('Xbmc executable existis %s' % xbmcExe)
		else:	
			fileCheckDialog(xbmcExe)

def UpdateCheck():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	date = ''
	datemodded = ''
	c = conn.cursor()
	mypath = steamWin.replace("BigBox.exe","") + "Data" + os.sep + "Platforms"
	for u in listdir(mypath):
		datemodded = time.ctime(os.path.getmtime(mypath + os.sep + u))
		platformxml = u.replace(".xml","")
		sql = "SELECT LastUpdate FROM updatelog where platform = " + "'" + platformxml + "'"
		c.execute(sql)
		results = c.fetchall()
		for row in results:
			date = row[0]
		if date == datemodded:
			same = "same"
		else:
			if dialog.yesno("BigBox", "One of your platforms have been updated, would you like to update the database?"):
				ResetDatabase(False)


	

def scriptVersionCheck():
	if scriptUpdateCheck == 'true':
		log('usr scripts are set to be checked for updates...')
		if delUserScriptSett == 'false':
			log('usr scripts are not set to be deleted, running version check')
			sysScriptDir = os.path.join(getAddonInstallPath(), 'resources', 'scripts')
			usrScriptDir = os.path.join(getAddonDataPath(), 'scripts')
			if osWin:
				sysScriptPath = os.path.join(sysScriptDir, 'SteamLauncher-AHK.ahk')
				usrScriptPath = os.path.join(usrScriptDir, 'SteamLauncher-AHK.ahk')
				if os.path.isfile(os.path.join(usrScriptPath)):
					compareFile(sysScriptPath, usrScriptPath)
				else:
					log('usr script does not exist, skipping version check')
			elif osLinux + osOsx:
				sysScriptPath = os.path.join(sysScriptDir, 'steam-launch.sh')
				usrScriptPath = os.path.join(usrScriptDir, 'steam-launch.sh')
				if os.path.isfile(os.path.join(usrScriptPath)):
					compareFile(sysScriptPath, usrScriptPath)
				else:
					log('usr script does not exist, skipping version check')
		else:
			log('usr scripts are set to be deleted, no version check needed')
	else:
		log('usr scripts are set to not be checked for updates, skipping version check')


def compareFile(sysScriptPath, usrScriptPath):
	global delUserScriptSett
	scriptSysVer = '000'
	scriptUsrVer = '000'
	if os.path.isfile(sysScriptPath):
		with open(sysScriptPath, 'r') as f:
			for line in f.readlines():
				if "BigBox.launcher.script.revision=" in line:
					scriptSysVer = line[32:35]
		log('sys "BigBox.launcher.script.revision=": %s' % scriptSysVer)
	if os.path.isfile(usrScriptPath):
		with open(usrScriptPath, 'r') as f:
			for line in f.readlines():
				if "BigBox.launcher.script.revision=" in line:
					scriptUsrVer = line[32:35]
		log('usr "BigBox.launcher.script.revision=": %s' % scriptUsrVer)
	if scriptSysVer > scriptUsrVer:
		log('system scripts have been updated: sys:%s > usr:%s' % (scriptSysVer, scriptUsrVer))
		if dialog.yesno(language(50113), language(50124), language(50125)):
			delUserScriptSett = 'true'
			log('yes selected, option delUserScriptSett enabled: %s' % delUserScriptSett)
		else:
			delUserScriptSett = 'false'
			log('no selected, script update check disabled: ScriptUpdateCheck = %s' % scriptUpdateCheck)
	else:
		log('userdata script are up to date')


def quitKodiDialog():
	global quitKodiSetting
	if quitKodiSetting == '2':
		log('quit setting: %s selected, asking user to pick' % quitKodiSetting)
		if dialog.yesno('Steam Launcher', language(50073)):
			quitKodiSetting = '0'
		else:
			quitKodiSetting = '1'
	log('quit setting selected: %s' % quitKodiSetting)


def kodiBusyDialog():
	if busyDialogTime != 0:
		xbmc.executebuiltin("ActivateWindow(busydialog)")
		log('busy dialog started')
		time.sleep(busyDialogTime)
		xbmc.executebuiltin("Dialog.Close(busydialog)")
		log('busy dialog stopped after: %s seconds' % busyDialogTime)


def steamPrePost():
	global postScript
	global preScript
	if preScriptEnabled == 'false':
		preScript = 'false'
	elif preScriptEnabled == 'true':
		if not os.path.isfile(os.path.join(preScript)):
			log('pre-steam script does not exist, disabling!: "%s"' % preScript)
			preScript = 'false'
			dialog.notification(language(50123), language(50126), addonIcon, 5000)
	elif preScript == '':
		preScript = 'false'
	log('pre steam script: %s' % preScript)
	if postScriptEnabled == 'false':
		postScript = 'false'
	elif preScriptEnabled == 'true':
		if not os.path.isfile(os.path.join(postScript)):
			log('post-steam script does not exist, disabling!: "%s"' % postScript)
			postScript = 'false'
			dialog.notification(language(50123), language(50126), addonIcon, 5000)
	elif postScript == '':
		postScript = 'false'
	log('post steam script: %s' % postScript)


def launchSteam():
	basePath = os.path.join(getAddonDataPath(), 'scripts')
	if osAndroid:
		cmd = "com.valvesoftware.android.steam.community"
		log('attempting to launch: "%s"' % cmd)
		xbmc.executebuiltin('XBMC.StartAndroidActivity("%s")' % cmd)
		kodiBusyDialog()
	elif osWin:
		steamlauncher = os.path.join(basePath, 'BigBoxLauncher-AHK.exe')
		cmd = '"%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (steamlauncher, steamWin, kodiWin, quitKodiSetting, kodiPortable, preScript, postScript)
		#log('Windows UTF-8 command: "%s"' % cmdutf8)
	elif osOsx:
		steamlauncher = os.path.join(basePath, 'steam-launch.sh')
		cmd = '"%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (steamlauncher, steamOsx, kodiOsx, quitKodiSetting, kodiPortable, preScript, postScript)
	elif osLinux:
		steamlauncher = os.path.join(basePath, 'steam-launch.sh')
		cmd = '"%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (steamlauncher, steamLinux, kodiLinux, quitKodiSetting, kodiPortable, preScript, postScript)
	try:
		print suspendAudio
		log('attempting to launch: %s' % cmd)
		print cmd.encode('utf-8')
		if suspendAudio == 'true':
			xbmc.audioSuspend()
			log('Audio suspended')
		if quitKodiSetting == '1' and suspendAudio == 'true':
			proc_h = subprocess.Popen(cmd.encode(txt_encode), shell=True, close_fds=False)
			kodiBusyDialog()
			log('Waiting for Steam to exit')
			while proc_h.returncode is None:
				xbmc.sleep(1000)
				proc_h.poll()
			log('Start resuming audio....')
			xbmc.audioResume()
			log('Audio resumed')
			del proc_h		
		else:
			subprocess.Popen(cmd.encode(txt_encode), shell=True, close_fds=True)
			kodiBusyDialog()


	except:
		log('ERROR: failed to launch: %s' % cmd)
		print cmd.encode(txt_encode)
		dialog.notification(language(50123), language(50126), addonIcon, 5000)



def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def addDir(name,url,mode,iconimage,fanart,description='',banner='',logo='',type='false'):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        contextMenuItems = []
        if type == "remove":
            contextMenuItems.append(("[COLOR orange]Remove Platform[/COLOR]",'XBMC.RunPlugin(%s?name=%s&url=%s&mode=67)'%(sys.argv[0], name.replace(',', ''), str(list))))
        elif type == "add":
            contextMenuItems.append(("[COLOR orange]Remove from Deleted Platforms[/COLOR]",'XBMC.RunPlugin(%s?name=%s&url=%s&mode=68)'%(sys.argv[0], name.replace(',', ''), str(list))))
        liz=xbmcgui.ListItem(name.strip(), iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.addContextMenuItems(contextMenuItems, replaceItems=False)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description} )
        liz.setProperty('fanart_image', fanart)
        liz.setArt({ 'clearart': logo, 'banner' : banner , 'clearlogo': logo})
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
		
mode = args.get('mode', None)

def addLink(name,url,mode,iconimage,fanart,description='',year='',dateadded='',lastplayed='',genre ='', rating='', banner='', logo='', trailer=''):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name.strip(), iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Year": year, "DateAdded": dateadded, "Genre": genre, "Mpaa": rating, "Trailer": trailer, "LastPlayed": lastplayed} )
        liz.setProperty('fanart_image', fanart)
        liz.setArt({ 'clearart': logo, 'banner' : banner , 'clearlogo': logo})
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
        return param
		
def INDEX():
	if osWin:
		addLink('Launch BigBox','url',100,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "bigbox" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "bigbox" + os.sep + "fanart.jpg",'Launches BigBox')
	addLink('Play Random Game','url',91,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "randomplay" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "randomplay" + os.sep + "fanart.jpg",'Selects a random game for you to play and launches it')
	addDir('Platform','url',2,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "platforms" + os.sep + "icon.jpg",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "platforms" + os.sep + "fanart.jpg",'Provides a list of all your Platforms in BigBox')
	addDir('Favorite','url',40,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "favorite" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "favorite" + os.sep + "fanart.jpg",'provides a list of all your games marked as favorte in BigBox')
	addDir('Genre','url',30,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "genre" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "genre" + os.sep + "fanart.jpg", 'lists all genres available for all games')
	addDir('Last Added','url',60,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "lastadded" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "lastadded" + os.sep + "fanart.jpg",'lists the last 100 games recently added to BigBox')
	addDir('Last Played','url',70,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "lastplayed" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "lastplayed" + os.sep + "fanart.jpg",'lists the last 100 games recently played in BigBox')
	addDir('Random Games','url',90,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "random" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "random" + os.sep + "fanart.jpg",'lists 100 random games')
	addDir('Search','url',80,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "search" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "search" + os.sep + "fanart.jpg",'allows you to search for a specific game')
	addDir('Update Database','url',51,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "updatedatabase" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images\updatedatabase" + os.sep + "fanart.jpg",'updates the addon database to match BigBox')
	addDir('Removed Platforms','url',4,addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "updatedatabase" + os.sep + "icon.png",addonPath + os.sep + "resources" + os.sep + "images\updatedatabase" + os.sep + "fanart.jpg",'updates the addon database to match BigBox')



def ResetDatabase(updater=False):
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	try:
		c.execute('''CREATE TABLE games
             (Title text, ApplicationPath text, Platform text, Emulator text,LastPlayedDate text,DateAdded text,Notes text, ReleaseDate text, Icon text, Fanart text, Completed text, Favorite text, Rating text, Genre text, Banner text, Logo text, Videos text)''')
	except:
		nothing = "nothing"
	try:
		c.execute('''CREATE TABLE platforms
             (Title text, Description text, Icon text, Fanart text, Banner text, Logo text)''')
	except:
		nothing = "nothing"
			
	try:
		c.execute('''CREATE TABLE emulatorcommands
             (Emulator text, Platform text, CommandLine text)''')
	except:
		nothing = "nothing"
		
	try:
		c.execute('''CREATE TABLE updatelog
             (Platform text, LastUpdate text)''')
	except:
		nothing = "nothing"
		
		
	try:
		c.execute('''CREATE TABLE removedplatforms
             (Platform text)''')
	except:
		nothing = "nothing"
		
	try:
		c.execute('''CREATE TABLE emulators
             (Emulator text, ApplicationPath text, CommandLine text)''')
	except:
		nothing = "nothing"		
		
	c.execute("delete from removedplatforms where Platform = 'Dont Remove This'")	
	c.execute("INSERT INTO removedplatforms VALUES('Dont Remove This')")
	mypath = steamWin.replace("BigBox.exe","") + "Data" + os.sep + "Platforms.xml"
	f = open(mypath, 'r')
	platform_as_string = f.read()
	root = ET.fromstring(platform_as_string)
	for title in root.findall('Platform'):
		imagespath = steamWin.replace("BigBox.exe","") + "Images" + os.sep + "Platforms"
		videospath = steamWin.replace("BigBox.exe","") + "Videos"
		try:
			platformname = title.find('Name').text
		except:
			platformname = ""
		
		try:
			platformdisc = title.find('Notes').text
			try:
				platformdisc = platformdisc.replace("'","''")
			except:
				platformdisc = "No Platform Information Found"
		except:
			platformdisc = "No Platform Information Found"
		
		try:
		
			if os.path.exists(imagespath + os.sep + platformname + os.sep + "Banner" + os.sep + platformname + ".jpg"):
				icon = (imagespath + os.sep + platformname + os.sep + "Banner" + os.sep + platformname + ".jpg")
			elif os.path.exists(imagespath + os.sep + platformname + os.sep + "Banner" + os.sep + platformname + ".png"):
				icon = (imagespath + os.sep + platformname + os.sep + "Banner" + os.sep + platformname + ".png")
			else:
				icon = (imagespath + os.sep + platformname + os.sep + "Banner" + os.sep + platformname + ".jpg")
		except:
			icon = 'default.png'
		
		try:
		
			if os.path.exists(imagespath + os.sep + platformname + os.sep + "Fanart" + os.sep + platformname + ".png"):
				fanart = (imagespath + os.sep + platformname + os.sep + "Fanart" + os.sep + platformname+ ".png")
			else:
				fanart = (imagespath + os.sep + platformname + os.sep + "Fanart" + os.sep + platformname+ ".jpg")
		
		except:
			fanart = 'default.png'
				
		try:
		
			if os.path.exists(imagespath + os.sep + platformname + os.sep + "Clear Logo" + os.sep + platformname + ".jpg"):
				logo = (imagespath + os.sep + platformname + os.sep + "Clear Logo" + os.sep + platformname + ".jpg")
			else:
				logo = (imagespath + os.sep + platformname + os.sep + "Clear Logo" + os.sep + platformname + ".png")
		
		except:
			logo = 'default.png'
			
		sql = "delete FROM platforms\
			WHERE Title = '%s'" % (platformname)
		c.execute(sql)
		DataString = (platformname + "','" + platformdisc + "','" + icon + "','" + fanart + "','" + icon + "','" + logo)
		c.execute("INSERT INTO platforms VALUES('" + DataString + "')")
		
	mypath = steamWin.replace("BigBox.exe","") + "Data" + os.sep + "Platforms"
	for u in listdir(mypath):
		datemodded = time.ctime(os.path.getmtime(mypath + os.sep + u))
		date = ''
		platformxml = u.replace(".xml","")
		hello = "never"
		sql = "SELECT LastUpdate FROM updatelog where platform = " + "'" + platformxml + "'"
		c.execute(sql)
		results = c.fetchall()
		for row in results:
			date = row[0]
		if date == datemodded:
			update = False
		else:
			update = True
		if osAndroid:
			update = True
		if updater == True:
			update = True
		if update == True:
			f = open(mypath + os.sep + u, 'r')
			gamename = "NULL"
			gamepath = "NULL"
			games_as_string = f.read()
			fanart = 'DefaultVideo.png'
			root = ET.fromstring(games_as_string)
			for title in root.findall('Game'):
				try:
					gametitle = title.find('Title').text
					gamename = title.find('Title').text
					try:
						gamename = gamename.replace("'","''")
					except:
						gamename = "NULL"
				except:
					gamename = "NULL"
				try:
					gamepath = title.find('ApplicationPath').text
					try: 
						gamepath = gamepath.replace("'","''")
					except:
						gamepath = "NULL"
				except:
					gamepath = "NULL"
				try:
					platform = title.find('Platform').text
					try:
						platform = platform.replace("'","''")
					except:
						platform = "NULL"
				except:
					platform = "NULL"
				try:
					lastplayed = title.find('LastPlayedDate').text
					try:
						lastplayed = lastplayed.replace("'","''")
					except:
						lastplayed = "NULL"
				except:
					lastplayed = "NULL"
				try:
					dateadded = title.find('DateAdded').text
					try:
						dateadded = dateadded.replace("'","''")
					except:
						dateadded = "NULL"
				except:
					dateadded = "NULL"
				try:
					Emulator = title.find('Emulator').text
					try:
						Emulator = Emulator.replace("'","''")
					except:
						Emulator = "NULL"
				except:
					Emulator = "NULL"
				try: 
					Discription = title.find('Notes').text
					try:
						Discription = Discription.replace("'","''")

					except:
						Discription = "No Game Information Found"
				except:
					Discription = "No Game Information Found"
		
				try:
					Year = title.find('ReleaseDate').text
					try:
						Year = Year.replace("'","''")
					except:
						Year = "NULL"
				except:
					Year = "NULL"
				
				try:
					Completed = title.find('Completed').text
					try:
						Completed = Completed.replace("'","''")
					except:
						Completed = "false"
				except:
					Completed = "false"
				
				
				try:
					Favorite = title.find('Favorite').text
					try:
						Favorite = Favorite.replace("'","''")
					except:
						Favorite = "false"
				except:
					Favorite = "false"
				
				try:
					Rating = title.find('Rating').text
					try:
						Rating = Rating.replace("'","''")
					except:
						Rating = "NULL"
				except:
					Rating = "NULL"
				
				try:
					Genre = title.find('Genre').text
					try:
						Genre = Genre.replace("'","''")
					except:
						Genre = "Unknown"
				except:
					Genre = "Unknown"
			
				try:
					iconappendb = gametitle.replace("'","_")
				except:
					iconappendb = gametitle
				try:
					iconappendb = iconappendb.replace(":","_")
				except:
					iconappendb = iconappendb
				try:
					iconappendb = iconappendb.replace("/","_")
				except:
					iconappendb = iconappendb
				imagespathg = steamWin.replace("BigBox.exe","") + "Images"
				videospath = steamWin.replace("BigBox.exe","") + "Videos"
				try:
				
					if os.path.exists(imagespathg + os.sep + platform + os.sep + "Fanart - Background" + os.sep + iconappendb + "-01.jpg"):
						fanart = (imagespathg + os.sep + platform + os.sep + "Fanart - Background" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Fanart - Background" + os.sep + iconappendb + "-01.png"):
						fanart = (imagespathg + os.sep + platform + os.sep + "Fanart - Background" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Screenshot - Gameplay" + os.sep + iconappendb + "-01.png"):
						fanart = (imagespathg + os.sep + platform + os.sep + "Screenshot - Gameplay" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Screenshot - Gameplay" + os.sep + iconappendb + "-01.jpg"):
						fanart = (imagespathg + os.sep + platform + os.sep + "Screenshot - Gameplay" + os.sep + iconappendb + "-01.jpg")
					else:
						fanart = 'default.png'
				except:
					fanart = 'default.png'
					
				try:
				
					if os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Asia" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Asia" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Asia" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Asia" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Australia" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Australia" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Australia" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Australia" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "China" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "China" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "China" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "China" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "France" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "France" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "France" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "France" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Germany" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Germany" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Germany" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Germany" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Italy" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Italy" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Italy" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Italy" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Korea" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Korea" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Korea" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Korea" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America, Europe" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America, Europe" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America, Europe" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America, Europe" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Spain" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Spain" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Spain" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Spain" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "The Netherlands" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "The Netherlands" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "The Netherlands" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "The Netherlands" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Japan" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Japan" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Japan" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Japan" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "North America" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "United States" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "United States" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "United States" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "United States" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Europe" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Europe" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Europe" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + "Europe" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Screenshot - Game Title" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Screenshot - Game Title" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Screenshot - Game Title" + os.sep + iconappendb + "-01.jpg"):
						icon = (imagespathg + os.sep + platform + os.sep + "Screenshot - Game Title" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + iconappendb + "-01.png"):
						icon = (imagespathg + os.sep + platform + os.sep + "Box - Front" + os.sep + iconappendb + "-01.png")
					else:
						icon = 'default.png'
				except:
					icon = 'default.png'
					
				try:
					video = (videospath + os.sep + platform + os.sep + iconappendb + '.mp4')
				except:
					video = 'default.mp4'
					
				try:
					if os.path.exists(imagespathg + os.sep + platform + os.sep + "Banner" + os.sep + iconappendb + "-01.png"):
						banner = (imagespathg + os.sep + platform + os.sep + "Banner" + os.sep + iconappendb + "-01.png")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Banner" + os.sep + iconappendb + "-01.jpg"):
						banner = (imagespathg + os.sep + platform + os.sep + "Banner" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.jpg"):
						banner = (imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.jpg")
					elif os.path.exists(imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.png"):
						banner = (imagespathg + os.sep + platform + os.sep + "Steam Banner" + os.sep + iconappendb + "-01.png")
					else:
						banner = 'default.png'
				except:
					banner = 'default.png'
					
				try:
				
					if os.path.exists(imagespathg + os.sep + platform + os.sep + "Clear Logo" + os.sep + iconappendb + "-01.jpg"):
						clearlogo = (imagespathg + os.sep + platform + os.sep + "Clear Logo" + os.sep + iconappendb + "-01.jpg")
					else:
						clearlogo = (imagespathg + os.sep + platform + os.sep + "Clear Logo" + os.sep + iconappendb + "-01.png")
				except:
					clearlogo = 'default.png'
					
				cmda = ""
				cmdb = ""
				apppath = ""
				if osLinux:
					gamepath = gamepath.replace("\\",os.sep)
				elif osAndroid:
					gamepath = gamepath.replace("\\",os.sep)
				pathjoin = os.path.join(steamWin.replace(os.sep + "BigBox.exe",""),gamepath)
				actualpath = os.path.normpath(pathjoin)
			
				sql = "delete FROM games\
					WHERE Platform = '%s' and Title = '%s'" % (platform, gamename)
				c.execute(sql)
				if CheckRomExists == 'true':
					if os.path.isfile(actualpath):
				
						DataString = (gamename + "','" + actualpath  + "','" + platform + "','" + Emulator + "','" + lastplayed[0:10] + "','" + dateadded[0:10] + "','" + Discription + "','" + Year[0:10] + "','" + icon + "','" + fanart + "','"  + Completed + "','" + Favorite + "','" + Rating + "','" + Genre + "','" + banner + "','" + clearlogo + "','" + video)
						c.execute("INSERT INTO games VALUES('" + DataString + "')")
				else:
					DataString = (gamename + "','" + actualpath  + "','" + platform + "','" + Emulator + "','" + lastplayed[0:10] + "','" + dateadded[0:10] + "','" + Discription + "','" + Year[0:10] + "','" + icon + "','" + fanart + "','"  + Completed + "','" + Favorite + "','" + Rating + "','" + Genre + "','" + banner + "','" + clearlogo + "','" + video)
					c.execute("INSERT INTO games VALUES('" + DataString + "')")
					
			c.execute("INSERT INTO updatelog VALUES('"+ platform + "','" + datemodded + "')")
			
			myemulators = steamWin.replace("BigBox.exe","") + "Data" + os.sep + "Emulators.xml" 
			f = open(myemulators, 'r')
			emulators_as_string = f.read()
			root = ET.fromstring(emulators_as_string)
			for title in root.findall('EmulatorPlatform'):
				try:
					emuid = title.find('Emulator').text
					try:
						emuid = emuid.replace("'","''")
					except:
						emuid = ""
				except:
					emuid = ""
				try:
					platformid = title.find('Platform').text
					try:
						platformid = platformid.replace("'","''")
					except:
						platformid = ""
				except:
					platformid = ""
				try:
					cmda = title.find('CommandLine').text
					try:
						cmda = cmda.replace("'","''")
					except:
						cmda = ""
				except:
					cmda = ""
					
				sql = "delete FROM emulatorcommands\
					WHERE Emulator = '%s' and Platform = '%s'" % (emuid,platformid)
				c.execute(sql)
				DataString = (emuid + "','" + platformid + "','" + cmda)
				c.execute("INSERT INTO emulatorcommands VALUES('" + DataString + "')")
					
					
		for emul in root.findall('Emulator'):	
			emuidl = emul.find('ID').text
			try:
				apppath = emul.find('ApplicationPath').text
				try:
					apppath = apppath.replace("'","''")
				except:
					apppath = ""
			except:
				apppath = ""
					
			try:	
				cmdb = emul.find('CommandLine').text
				try:
					cmdb = cmdb.replace("'","''")
				except:
					cmdb = ""
			except:
				cmdb = ""
					
			try:
				apppath = apppath.replace("\\",os.sep)
				pathjoin = os.path.join(steamWin.replace(os.sep + "BigBox.exe",""),apppath)
				actualemupath = os.path.normpath(pathjoin)
			except:
				actualemupath = apppath

			commandb = cmdb.replace("%launchboxorbigboxexepath%",steamWin)
			
			sql = "delete FROM emulators\
				WHERE Emulator = '%s'" % (emuidl)
			c.execute(sql)
			DataString = (emuidl + "','" + actualemupath + "','" + commandb)
			c.execute("INSERT INTO emulators VALUES('" + DataString + "')")
	conn.commit()
	conn.close()
	dialog.ok("BigBox","Update Complete")
	
	
def test():
	steamPrePost()
	quitKodiDialog()
	launchSteam()
	
def RemovePlatform(url):
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	c.execute("INSERT INTO removedplatforms VALUES('" + url + "')")
	conn.commit()
	conn.close()
	dialog.ok("Big Box","Removed " + url)

def EnablePlatform(url):
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	c.execute("delete from removedplatforms where Platform = '" + url + "'")
	conn.commit()
	conn.close()
	dialog.ok("Big Box","Removed " + url)
	
def GenreList():	
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	sql = "WITH RECURSIVE split(content, last, rest) AS (select '' as content,'' as last, Genre as rest from games UNION ALL SELECT CASE WHEN last = ';' THEN substr(rest, 1, 1) ELSE content || substr(rest, 1, 1) END, substr(rest, 1, 1), substr(rest, 2) FROM split WHERE rest <> '') SELECT distinct REPLACE(content, ';','') AS 'ValueSplit' FROM split WHERE last = ';' OR rest ='';"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		icon = addonPath + os.sep + "resources" + os.sep + "images" + os.sep + "genre" + os.sep + name + ".png"
		addDir(name,name,31,icon,fanart,"")
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATEADDED)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LASTPLAYED)
	conn.close()

def platformList():	
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	sql = "SELECT * FROM platforms where Title not in (select Platform from removedplatforms)"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		description = row[1]
		icon = row[2]
		fanart = row[3]
		banner = row[4]
		logo = row[5]
		sqlp = "SELECT * FROM games WHERE platform = '%s' and Fanart != 'default.png' ORDER BY RANDOM() LIMIT 10" % (name)
		c.execute(sqlp)
		results = c.fetchall()
		for row in results:
			fanart = row[9]
		addDir(name,name,3,icon,fanart,description,banner,logo,"remove")
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATEADDED)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LASTPLAYED)
	conn.close()
	
def deletedplatformList():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	sql = "select * from removedplatforms"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		addDir(name,name,3,'default.png','default.png','none','none','none',"add")
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATEADDED)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LASTPLAYED)
	conn.close()


def GameListGenre(Genre):
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	if NoArtworkEnabled == 'true':
		sql = "SELECT * FROM games\
		   WHERE genre like '%s' and Platform not in (select Platform from removedplatforms)" % (Genre)
	else:
		sql = "SELECT * FROM games\
		   WHERE genre like '%s' and Icon != 'default.png' and Platform not in (select Platform from removedplatforms)" % (Genre)
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator,5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATEADDED)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LASTPLAYED)
	conn.close()	
	
def GameListPlatform(Platform):
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	if NoArtworkEnabled == 'true':
		sql = "SELECT * FROM games\
		   WHERE platform = '%s' and Platform not in (select Platform from removedplatforms)" % (Platform)
	else:
		sql = "SELECT * FROM games\
		   WHERE platform = '%s' and Icon != 'default.png' and Platform not in (select Platform from removedplatforms)" % (Platform)
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator,5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATEADDED)
		xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LASTPLAYED)
	conn.close()

def search_game(query):
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	query = query.replace("'","''")
	if NoArtworkEnabled == 'true':
		sql = "select * from games where Title like '%" + query + "%' and Platform not in (select Platform from removedplatforms)"
	else:
		sql = "select * from games where Title like '%" + query + "%' and Icon != 'default.png' and Platform not in (select Platform from removedplatforms)"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator,5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
	conn.close()
	
def GameListLastAdded():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	if NoArtworkEnabled == 'true':
		sql = "select * from games where DateAdded != 'NULL' and Platform not in (select Platform from removedplatforms) order by DateAdded desc LIMIT 100"
	else:
		sql = "select * from games where DateAdded != 'NULL' and Icon != 'default.png' and Platform not in (select Platform from removedplatforms) order by DateAdded desc LIMIT 100"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator,5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
	conn.close()

	
	
def GameListFavorite():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	if NoArtworkEnabled == 'true':
		sql = "select * from games where Favorite != 'false' and Platform not in (select Platform from removedplatforms) LIMIT 100"
	else:
		sql = "select * from games where Favorite != 'false' and Icon != 'default.png' and Platform not in (select Platform from removedplatforms) LIMIT 100"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator, 5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
	conn.close()	
	
def GameListLastPlayed():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	if NoArtworkEnabled == 'true':
		sql = "select * from games where LastPlayedDate != 'NULL' and Platform not in (select Platform from removedplatforms) order by LastPlayedDate desc LIMIT 100"
	else:
		sql = "select * from games where LastPlayedDate != 'NULL' and Icon != 'default.png' and Platform not in (select Platform from removedplatforms) order by LastPlayedDate desc LIMIT 100"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator, 5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
	conn.close()
	
	
def GameListRandom():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	if NoArtworkEnabled == 'true':
		sql = "select * from games where Platform not in (select Platform from removedplatforms) ORDER BY RANDOM() LIMIT 100"
	else:
		sql = "select * from games where Icon != 'default.png' and Platform not in (select Platform from removedplatforms) ORDER BY RANDOM() LIMIT 100"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
		addLink(name,"ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator, 5,icon,fanart,Notes,ReleaseDate,DateAdded,LastPlayed,genre,rating,banner,logo,video)
	conn.close()
	
def GameRandomPlay():
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	sql = "select * from games where Platform not in (select Platform from removedplatforms) ORDER BY RANDOM() LIMIT 100"
	c.execute(sql)
	results = c.fetchall()
	for row in results:
		name = row[0]
		ApplicationPath = row[1]
		Platform = row[2]
		Emulator = row[3]
		LastPlayed = row[4]
		DateAdded = row[5]
		Notes = row[6]
		ReleaseDate = row[7]
		icon = row[8]
		fanart = row[9]
		rating = row[12]
		genre = row[13]
		banner = row[14]
		logo = row[15]
		video = row[16]
	conn.close()
	LaunchGame("ApplicationPath=" + ApplicationPath + "&Platform=" + Platform + "&Emulator=" + Emulator)

def search():
    keyboard = xbmc.Keyboard('', "Search Game", False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
        if len(query) > 0:
            search_game(query)

	
	
def LaunchGame(url):
	gamepath = re.findall("ApplicationPath="+"(.*)"+"&Platform=",url)[0]
	emulator = re.findall("&Emulator="+"(.*)"+"",url)[0]
	platform = re.findall("&Platform="+"(.*)"+"&Emulator=",url)[0]
	DatabasePath = os.path.join(getAddonDataPath(), 'database.db')
	conn = sqlite3.connect(DatabasePath)
	c = conn.cursor()
	sql = "select * from emulators where Emulator = '%s'" % (emulator)
	c.execute(sql)
	results = c.fetchall()
	try:
		ApplicationPath =  results[0][1]
	except:
		ApplicationPath = ""
		
	try:
		ApplicationPathFixed = '"' + results[0][1] + '"'
	except:
		ApplicationPathFixed = ""
		
	try:
		Commanda = results[0][2]
	except:
		Commanda =""
		
	sqlb = "select CommandLine from emulatorcommands where Emulator = '%s' and Platform = '%s'" % (emulator,platform)
	c.execute(sqlb)
	resultsb = c.fetchall()
	try:
		Commandb = resultsb[0][0]
	except:
		Commandb = ""
	
	join = Commanda + Commandb
	commandc = join.replace("%platform%",platform)
	if osLinux:
		ApplicationPathFixed = os.path.basename(ApplicationPathFixed)
		ApplicationPathFixed = ApplicationPathFixed.replace(".exe","")
		ApplicationPathFixed = ApplicationPathFixed.replace('"',"")
		commandc = commandc.replace("\\",os.sep)
		commandc = commandc.replace("cores","/usr/lib/libretro")
		commandc = commandc.replace(".dll",".so")
		listitem = ApplicationPathFixed + " " + commandc + ' "' + gamepath + '"'
		inipath = os.path.join(getAddonInstallPath(), 'resources','linuxcom.xml')
		f = open(inipath, 'r')
		command_as_string = f.read()
		root = ET.fromstring(command_as_string)
		for title in root.findall('Platform'):
			try:
				platformname = title.find('Name').text
			except:
				platformname = ""
			try:
				command = title.find('Command').text
			except:
				command = ""
				
			if platformname == platform:
				listitem = command.replace("%ROM_PATH%", gamepath)
	elif osAndroid:
		ApplicationPathFixed = os.path.basename(ApplicationPathFixed)
		ApplicationPathFixed = ApplicationPathFixed.replace(".exe","")
		ApplicationPathFixed = ApplicationPathFixed.replace('"',"")
		commandc = commandc.replace("\\",os.sep)
		commandc = commandc.replace('-L "cores/',"")
		commandc = commandc.replace('.dll"',"")
		listitem = "/system/bin/am start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -e ROM " + '"' + gamepath + '"' + " -e CONFIGFILE /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg -e LIBRETRO /data/data/com.retroarch/cores/" + commandc + "_android.so -e IME com.android.inputmethod.latin/.LatinIME -n com.retroarch/.browser.retroactivity.RetroActivityFuture"
		inipath = os.path.join(getAddonInstallPath(), 'resources','androidcom.xml')
		f = open(inipath, 'r')
		command_as_string = f.read()
		root = ET.fromstring(command_as_string)
		for title in root.findall('Platform'):
			try:
				platformname = title.find('Name').text
			except:
				platformname = ""
			try:
				command = title.find('Command').text
			except:
				command = ""
				
			if platformname == platform:
				listitem = command.replace("%ROM_PATH%", gamepath)
				dialog.ok("Heading", listitem)
	else:
		listitem = ApplicationPathFixed + " " + commandc + ' "' + gamepath + '"'
	basePath = os.path.join(getAddonDataPath(), 'scripts')
	steamlauncher = os.path.join(basePath, 'BigBoxLauncher-AHK.exe')
	cmd = listitem.replace("  "," ")
	if cmd[0] == ' ':
		cmd = cmd[1:]
	
	if cmd[0:6] == '"steam':
		cmd = "explorer.exe " + cmd

	workingdir = os.path.dirname(ApplicationPath)
	if workingdir == "":
		workingdir = "c:" + os.sep + "windows" + os.sep + "system32"
	try:
		if osAndroid:
			xbmc.audioSuspend()
			xbmc.enableNavSounds(False)
			xbmc.sleep(500) #This pause seems to help... I'm not really sure why
			try:
				execute_subprocess_command(listitem.encode('utf-8'))
			except:
				os.system(listitem.encode('utf-8'))
			xbmc.audioResume()
			xbmc.enableNavSounds(True)
		
		else:
		
			print suspendAudio
			log('attempting to launch: %s' % cmd)
			print cmd.encode('utf-8')
			if suspendAudio == 'true':
				xbmc.audioSuspend()
				log('Audio suspended')
			if quitKodiSetting == '1' and suspendAudio == 'true':
				proc_h = subprocess.Popen(cmd.encode(txt_encode), cwd=workingdir, shell=True, close_fds=False)
				kodiBusyDialog()
				log('Waiting for Steam to exit')
				while proc_h.returncode is None:
					xbmc.sleep(1000)
					proc_h.poll()
				log('Start resuming audio....')
				xbmc.audioResume()
				log('Audio resumed')
				del proc_h		
			else:
				subprocess.Popen(cmd.encode(txt_encode), cwd=workingdir, shell=True, close_fds=True)
				kodiBusyDialog()


	except:
		log('ERROR: failed to launch: %s' % cmd)
		print cmd.encode(txt_encode)
		dialog.notification(language(50123), language(50126), addonIcon, 5000)
		
	conn.close()

	
	

		
log('****Running Steam-Launcher v%s....' % addonVersion)
log('running on osAndroid, osOsx, osLinux, osWin: %s %s %s %s ' % (osAndroid, osOsx, osLinux, osWin))
log('System text encoding in use: %s' % txt_encode)

scriptVersionCheck()
usrScriptDelete()
copyLauncherScriptsToUserdata()
fileChecker()
makeScriptExec()

params=get_params(); url=None; name=None; mode=None; site=None; iconimage=None
try: site=urllib.unquote_plus(params["site"])
except: pass
try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except: pass
try: iconimage=urllib.unquote_plus(params["iconimage"])
except: pass

if mode==None or url==None or len(url)<1: INDEX()
elif mode==2: platformList()
elif mode==4: deletedplatformList()
elif mode==30: GenreList()
elif mode==31: GameListGenre(url)
elif mode==3: GameListPlatform(url)
elif mode==5: LaunchGame(url)
elif mode==40: GameListFavorite()
elif mode==50: ResetDatabase(False)
elif mode==51: ResetDatabase(True)
elif mode==60: GameListLastAdded()
elif mode==67: RemovePlatform(name)
elif mode==68: EnablePlatform(name)
elif mode==70: GameListLastPlayed()
elif mode==90: GameListRandom()
elif mode==91: GameRandomPlay()
elif mode==80: search()
elif mode==100: test()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
