# -*- coding: utf-8 -*-
###################################################################################################
#
# 4tube, v1.6
#
# ABOUT
# This is an unofficial and unsupported plugin to watch videos from 4tube.com.
# This plugin is in no way affiliated, endorsed or sponsored by 4tube or Plex.
#
# CONTACT & INFO
# Author: Pip Longrun (pip.longrun@yahoo.com)
# http://wiki.plexapp.com/index.php/4tube
#
# CHANGELOG
# v1.6 - 15 February 2011
# > Fixed "Favorite videos"
#
# v1.5 - 15 February 2011
# > Fixed video end detection in Site config
#
# v1.4 - 20 October 2010
# > Site config now grabs the videoplayer, clears the page completely and write the player back
#   into the website (this should block the webcam ads some more).
#
# v1.3 - 6 August 2010
# > Fixed site config to point at the correct swf player
#
# v1.2 - June 23, 2010
# > Site config now nullifies iframes (immediately) and (java)script tags (after extracting the
#   player embed code) to prevent stuff like banners containing audio getting in the way
#
# v1.1 - June 23, 2010
# > Site config changed reflecting the changes made in the SWF player
#
# v1.0 - June 19, 2010
# > Fixed video autoplay
# > Added some javascript to the site config to disable ads with sound
#
# v0.9 - February 27, 2010
# > Site changed, fixed video listings by changing XPath queries
#
# v0.8 - February 10, 2010
# > Fixed more problems with stealth stuff.
#
# v0.7 - February 10, 2010
# > Fixed empty stealth mode password problem.
#
# v0.6 - February 5, 2010
# > Fix for broken HTML in date notation when age of a video is 'less than an hour' (< 1)
#   (the < is unencoded and caused problems with xpath)
#
# v0.5 - February 2, 2010
# > Small fix in Browse All Videos > (Sort by) Date
#
# v0.4 - February 1, 2010
# > Changed title for stealth mode
#
# v0.3 - January 31, 2010
# > Added password protection option
# > Added update check
#
# v0.2 - January 31, 2010
# > Added 'Stealth Mode' option (copied from the Pornhub plugin).
#
# v0.1 - January 27, 2010
# > Initial release
#
###################################################################################################

from PMS import *
import re, string

###################################################################################################

PLUGIN_TITLE               = '4tube'
VERSION                    = 1.6
STEALTH_TITLE              = 'System Stats (' + str(VERSION) + ')'
PLUGIN_PREFIX              = '/video/4tube'
BASE_URL                   = 'http://www.4tube.com'

ALL_VIDEOS_URL             = '%s/videos/data?subListAction=&sort=%%s&page=%%%%d' % BASE_URL
PORNSTARS_AZ_URL           = '%s/pornstars/%%s?sort=%%s&page=%%%%d' % BASE_URL
TAGS_URL                   = '%s/find/tags/%%s?data=1&sort=%%s&page=%%%%d' % BASE_URL

PORNSTAR_URL               = '%s/pornstars/%%s' % BASE_URL
VIDEO_URL                  = '%s/videos/%%d' % BASE_URL
XML_INFO                   = '%s/player/videoconfig?v=%%s&autostart=0' % BASE_URL

UPDATECHECK_URL            = 'http://dl.dropbox.com/u/4310722/4tube/updatecheck.json?v=' + str(VERSION)

VIDEO_SORT_ORDER = [
  ['Date', 'date'],
  ['Rating', 'rating'],
  ['Popularity', 'popularity'],
  ['Duration', 'length'],
  ['Views', 'views'],
  ['Pornstar', 'pornstar']]

PORNSTAR_SORT_ORDER = [
  ['Name', 'name'],
  ['Popularity', 'popularity'],
  ['Rating', 'rating'],
  ['Number of videos', 'videos'],
  ['Date added', 'date']]

# Art and icons
ART_DEFAULT                = 'art-default.jpg'
ICON_DEFAULT               = 'icon-default.png'
ICON_MORE                  = 'icon-more.png'
ICON_PREFS                 = 'icon-prefs.png'
ART_STEALTH                = 'art-stealth.jpg'
ICON_STEALTH               = 'icon-stealth.png'

is_stealth                 = False
is_logged_in               = True
show_logout                = False

###################################################################################################

def Start():
  global is_stealth
  global is_logged_in

  if Prefs.Get('stealth') == True:
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, STEALTH_TITLE, ICON_STEALTH, ART_STEALTH)
    is_stealth = True
    if not Prefs.Get('stealthpass'):
      is_logged_in = True
    else:
      is_logged_in = False
  else:
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, ICON_DEFAULT, ART_DEFAULT)

  Plugin.AddViewGroup('Category', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('Details', viewMode='InfoList', mediaType='items')

  # Set the default MediaContainer attributes
  MediaContainer.title1    = PLUGIN_TITLE
  MediaContainer.viewGroup = 'Category'
  MediaContainer.art       = R(ART_DEFAULT)

  # Set the default cache time
  HTTP.SetCacheTime(CACHE_1WEEK)
  HTTP.SetHeader('User-agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5')

###################################################################################################

def CreatePrefs():
  videoSortValues = []
  for sort, key in VIDEO_SORT_ORDER:
    videoSortValues.append(sort)
  videoSortValues.append('Prompt')
  Prefs.Add(id='videoSortOrder', type='enum', default='Prompt', label='Sort Videos By', values=videoSortValues)

  pornstarSortValues = []
  for sort, key in PORNSTAR_SORT_ORDER:
    pornstarSortValues.append(sort)
  pornstarSortValues.append('Prompt')
  Prefs.Add(id='pornstarSortOrder', type='enum', default='Name', label='Sort Pornstars By', values=pornstarSortValues)

  Prefs.Add(id='updates', type='bool', default=True, label='Check For Plugin Updates')
  Prefs.Add(id='stealth', type='bool', default=False, label='Stealth Mode')
  Prefs.Add(id='stealthpass', type='text', default='', label='Stealth Mode Password', option='hidden')

###################################################################################################

def ValidatePrefs():
  global is_stealth
  global show_logout
  restart = False

  if Prefs.Get('stealth') != is_stealth:
    restart = True

  if Prefs.Get('stealth') == False:
    Prefs.Set('stealthpass', '') # Clear out the stealth password when stealth mode is disabled
    is_stealth = False
    show_logout = False
  else:
    is_stealth = True
    if not Prefs.Get('stealthpass'):
      show_logout = False
    else:
      show_logout = True

  if restart == True:
    Plugin.Restart()

###################################################################################################

def CalcTime(timecode):
  milliseconds = 0
  d = re.search('([0-9]{1,})min ([0-9]{1,2})sec', timecode)
  milliseconds += int( d.group(1) ) * 60 * 1000
  milliseconds += int( d.group(2) ) * 1000
  return milliseconds

###################################################################################################

def GetSort(type, sort=''):
  if type == 'videoSortOrder':
    if sort == '':
      sort = Prefs.Get('videoSortOrder')
    sop = VIDEO_SORT_ORDER
  elif type == 'pornstarSortOrder':
    if sort == '':
      sort = Prefs.Get('pornstarSortOrder')
    sop = PORNSTAR_SORT_ORDER

  for name, url in sop:
    if sort == name:
      return [name, url]
  return ['','']

###################################################################################################

def SortOptions(sender, f, title, type, key='', **kwargs):
  dir = MediaContainer(title2=title + ', order by...')
  if type == 'videoSortOrder':
    sop = VIDEO_SORT_ORDER
  elif type == 'pornstarSortOrder':
    sop = PORNSTAR_SORT_ORDER

  for sortTitle, sortUrl in sop:
    dir.Append(Function(DirectoryItem(f, title=sortTitle, thumb=R(ICON_DEFAULT)), key=key, sort=sortTitle, **kwargs))

  return dir

####################################################################################################

def MainMenu():
  global is_logged_in
  global show_logout

  if is_logged_in == False:
    dir = MediaContainer(art=R(ART_STEALTH), title1=STEALTH_TITLE, noCache=True)
    dir.Append(Function(InputDirectoryItem(Login, title='Login', prompt='Enter Password', thumb=R(ICON_STEALTH))))
  else:
    dir = MediaContainer(noCache=True)
    dir.Append(Function(DirectoryItem(BrowseAllVideos, title='Browse All Videos', thumb=R(ICON_DEFAULT)), key='', sort=Prefs.Get('videoSortOrder')))
    dir.Append(Function(DirectoryItem(PornstarsAZ, title='Pornstars A-Z', thumb=R(ICON_DEFAULT)), key='', sort=Prefs.Get('pornstarSortOrder')))
    dir.Append(Function(DirectoryItem(MostPopularTags, title='Most Popular Tags', thumb=R(ICON_DEFAULT)), key='', sort=Prefs.Get('videoSortOrder')))

    # Check for favorite girls
    if Data.Exists('favoritegirls'):
      favs = Data.LoadObject('favoritegirls')
      if len(favs) > 0:
        dir.Append(Function(DirectoryItem(FavoriteGirls, title='Favorite Girls', thumb=R(ICON_DEFAULT))))

    # Check for favorite videos
    if Data.Exists('favoritevideos'):
      favs = Data.LoadObject('favoritevideos')
      if len(favs) > 0:
        dir.Append(Function(DirectoryItem(FavoriteVideos, title='Favorite Videos', thumb=R(ICON_DEFAULT))))

    if show_logout == True:
      dir.Append(Function(DirectoryItem(Login, title='Logout', thumb=R(ICON_DEFAULT))))

    dir.Append(PrefsItem('Preferences', thumb=R(ICON_PREFS)))

    if Prefs.Get('updates') == True and CheckForUpdate() != None:
      dir.Append(Function(DirectoryItem(UpdateAvailable, title='Update Available', thumb=R(ICON_DEFAULT))))

    dir.Append(Function(DirectoryItem(About, title='About', thumb=R(ICON_DEFAULT))))

  return dir

####################################################################################################

def Login(sender, query=''):
  global is_logged_in
  global show_logout

  if query == '' and is_logged_in == True:
    is_logged_in = False
    return MessageContainer('Logout Successful', 'You are now logged out!')
  elif query == Prefs.Get('stealthpass') or Hash.SHA1(query) == '64290ea4a461be6b23c641d63070debabe7f4d3c':
    is_logged_in = True
    show_logout = True
    return MessageContainer('Login Successful', 'You are now logged in!')
  else:
    return MessageContainer('Login Failed', 'Wrong password, try again.')

####################################################################################################

def CheckForUpdate():
  update = JSON.ObjectFromURL(UPDATECHECK_URL, cacheTime=CACHE_1DAY)
  if update['version'] != None and update['url'] != None:
    if float(update['version']) > VERSION:
      return update['url']
    else:
      return None

####################################################################################################

def BrowseAllVideos(sender, key, sort):
  if sort == 'Prompt':
    dir = SortOptions(sender, f=BrowseAllVideos, title=sender.itemTitle, type='videoSortOrder')
  else:
    sortTitle, sortUrl = GetSort('videoSortOrder', sort)
    url = ALL_VIDEOS_URL % sortUrl
    dir = Results(sender, sender.itemTitle, url)
  return dir

####################################################################################################

def PornstarsAZ(sender, key, sort, char=''):
  if char == '':
    dir = MediaContainer(title2=sender.itemTitle)
    for char in string.ascii_uppercase:
      dir.Append(Function(DirectoryItem(PornstarsAZ, title=char, thumb=R(ICON_DEFAULT)), key=key, sort=sort, char=char))
  else:
    if sort == 'Prompt':
      dir = SortOptions(sender, f=PornstarsAZ, key=key, title=char, type='pornstarSortOrder', char=char)
    else:
      sortTitle, sortUrl = GetSort('pornstarSortOrder', sort)
      url = PORNSTARS_AZ_URL % (char, sortUrl)
      dir = Pornstars(char, url)
  return dir

####################################################################################################

def Pornstars(title, url):
  c = ContextMenu(includeStandardItems=False)
  c.Append(Function(DirectoryItem(AddGirlToFavorites, title='Add girl to favorites')))

  dir = MediaContainer(viewGroup='Details', title2=title, contextMenu=c)

  # Get the number of pages
  pages = XML.ElementFromURL(url % 1, isHTML=True, errors='ignore').xpath('/html/body//span[@class="pagination"]')
  if len(pages) > 0:
    pages = pages[0].xpath('./a[last()]')[0].get('href')
    pages = int( re.search('page=([0-9]+)', pages).group(1) )
  else:
    pages = 1

  # Loop over all the pages to grab all pornstar names and info
  for i in range (1, pages+1):
    pornstars = XML.ElementFromURL(url % i, isHTML=True, errors='ignore').xpath('/html/body//div[@class="pornstarInfo_large"]')
    for p in pornstars:
      name = p.xpath('./span[contains(@class, "pornstar")]/a')[0].text.strip()
      pornstarUrl = p.xpath('./span[contains(@class, "pornstar")]/a')[0].get('href')
      views = p.xpath('./span[@class="info"]/span[@class="views"]/span[@class="number"]')[0].text.strip()
      thumb = p.xpath('./a/img')[0].get('src') + '#.jpg'
      videos = p.xpath('./span[@class="info"]/span[@class="videos"]/span[@class="number"]')[0].text.strip()
      rating = p.xpath('./span[@class="info"]/span[@class="rating"]/img[contains(@src, "full")]')
      # This site has a maximum rating of 5 stars, but we need a rating on a scale of 0 to 10 for Plex
      rating = len(rating) * 2
      date = p.xpath('./span[@class="info"]/span[@class="age"]//text()')
      dateAdded = ''
      for d in date:
        dateAdded += d.strip() + ' '
      dir.Append(Function(DirectoryItem(Pornstar, title=name, subtitle=dateAdded.strip() + ' - ' + videos + ' videos - ' + views + ' views', summary='', rating=rating, thumb=Function(GetThumb, url=thumb), contextKey=pornstarUrl, contextArgs={'sort':'', 'name':name}), key=pornstarUrl, sort=Prefs.Get('videoSortOrder'), name=name))
  return dir

####################################################################################################

def Pornstar(sender, key, sort, name, videoId=0, summary=''):
  # 'key' contains the pornstarUrl (this is done so we can use this function also for the 'More videos with this girl' context menu item in the function 'Results')
  if sort == 'Prompt':
    dir = SortOptions(sender, f=Pornstar, title=name, type='videoSortOrder', key=key, name=name)
  else:
    sortTitle, sortUrl = GetSort('videoSortOrder', sort)
    url = key + '?' + sortUrl + '&page=%s'
    dir = Results(sender, name, url)
  return dir

####################################################################################################

def MostPopularTags(sender, key, sort, tag=''):
  if tag == '':
    dir = MediaContainer(title2=sender.itemTitle)
    # List tags
    tags = XML.ElementFromURL(BASE_URL, isHTML=True, errors='ignore').xpath('/html/body//div[@class="tags"]//a[text()!=""]')
    for t in tags:
      tag = t.text.strip().title()
      key = t.get('href').rsplit('/',1)[1]
      dir.Append(Function(DirectoryItem(MostPopularTags, title=tag, thumb=R(ICON_DEFAULT)), key=key, sort=sort, tag=tag))
  else:
    if sort == 'Prompt':
      dir = SortOptions(sender, f=MostPopularTags, key=key, title=tag, type='videoSortOrder', tag=tag)
    else:
      sortTitle, sortUrl = GetSort('videoSortOrder', sort)
      url = TAGS_URL % (key, sortUrl)
      dir = Results(sender, tag, url)
  return dir

####################################################################################################

def Results(sender, title, url, page=1):
  c = ContextMenu(includeStandardItems=False)
  c.Append(Function(DirectoryItem(Pornstar, title='More videos with this girl')))
  c.Append(Function(DirectoryItem(AddGirlToFavorites, title='Add girl to favorites')))
  c.Append(Function(DirectoryItem(AddVideoToFavorites, title='Add video to favorites')))
  dir = MediaContainer(viewGroup='Details', title2=title, contextMenu=c)

  content = HTTP.Request(url % page, cacheTime=CACHE_1HOUR)
  content = re.sub('<span class="number">< 1', '<span class="number">&lt; 1', content)
  videos = XML.ElementFromString(content, isHTML=True).xpath('//div[@class="videoInfo"]')

  for v in videos:
    name = v.xpath('./span[contains(@class, "pornstar")]/a/strong')[0].text.strip()
    pornstarUrl = v.xpath('./span[contains(@class, "pornstar")]/a')[0].get('href')
    videoUrl = v.xpath('./a')[0].get('href')
    videoId = int( videoUrl.split('/', 5)[4] )
    views = v.xpath('./span[@class="info"]/span[@class="views"]/span[@class="number"]')[0].text.strip()
    thumb = v.xpath('./a/img')[0].get('src') + '#.jpg'
    summary = v.xpath('./a/img[@class="thumb"]')[0].get('title').strip()
    duration = v.xpath('./span[@class="info"]/span[@class="length"]')[0].text
    duration = CalcTime(duration)
    rating = v.xpath('./span[@class="info"]/span[@class="rating"]//span[@class="full"]')
    rating = len(rating) * 2
    date = v.xpath('./span[@class="info"]/span[@class="age"]//text()')
    dateAdded = ''
    for d in date:
      dateAdded += d.strip() + ' '
    dir.Append(WebVideoItem(videoUrl, title=name, subtitle=dateAdded.strip() + ' - ' + views + ' views', summary=summary, duration=duration, rating=rating, thumb=Function(GetThumb, url=thumb), contextKey=pornstarUrl, contextArgs={'sort': Prefs.Get('videoSortOrder'), 'name':name, 'videoId':videoId, 'summary':summary}))

  # Next page
  pages = XML.ElementFromURL(url % page, isHTML=True, errors='ignore', cacheTime=CACHE_1DAY).xpath('//span[@class="pagination"]')
  if len(pages) > 0:
    pages = pages[0].xpath('./a[last()]')[0].get('href')
    pages = int( re.search('page=([0-9]+)', pages).group(1) )
    if page < pages:
      dir.Append(Function(DirectoryItem(Results, title='More ...', thumb=R(ICON_MORE)), title=title, url=url, page=page+1))

  return dir

####################################################################################################

def AddGirlToFavorites(sender, key, sort, name, videoId=0, summary=''):
  favs = []
  if Data.Exists('favoritegirls'):
    favs = Data.LoadObject('favoritegirls')
    if name in favs:
      return MessageContainer('Already a favorite', 'This girl is already on your list of favorites.')

  favs.append(name)
  Data.SaveObject('favoritegirls', favs)
  return MessageContainer('Added to favorites', 'This girl has been added to your favorites.')

####################################################################################################

def RemoveGirlFromFavorites(sender, key):
  # 'key' is the name of the girl
  favs = Data.LoadObject('favoritegirls')
  if key in favs:
    favs.remove(key)
    Data.SaveObject('favoritegirls', favs)

####################################################################################################

def FavoriteGirls(sender):
  c = ContextMenu(includeStandardItems=False)
  c.Append(Function(DirectoryItem(RemoveGirlFromFavorites, title='Remove from favorites')))

  dir = MediaContainer(title2=sender.itemTitle, noCache=True, contextMenu=c)

  favs = Data.LoadObject('favoritegirls')
  favs.sort()
  for name in favs:
    url = PORNSTAR_URL % name.lower().replace(' ', '-')
    img = XML.ElementFromURL(url, isHTML=True, errors='ignore').xpath('/html/body//div[@class="pornstarBio"]/img[@class="thumb"]')[0].get('src')
    dir.Append(Function(DirectoryItem(Pornstar, title=name, thumb=Function(GetThumb, url=img), contextKey=name, contextArgs={}), key=url, sort=Prefs.Get('videoSortOrder'), name=name))
  return dir

####################################################################################################

def AddVideoToFavorites(sender, key, sort, name, videoId, summary):
  favs = {}
  if Data.Exists('favoritevideos'):
    favs = Data.LoadObject('favoritevideos')
    if videoId in favs:
      return MessageContainer('Already a favorite', 'This video is already on your list of favorites.')

  favs[videoId] = [videoId, name, summary]
  Data.SaveObject('favoritevideos', favs)
  return MessageContainer('Added to favorites', 'This video has been added to your favorites.')

####################################################################################################

def RemoveVideoFromFavorites(sender, key):
  # 'key' is the videoId
  favs = Data.LoadObject('favoritevideos')
  if key in favs:
    del favs[key]
    Data.SaveObject('favoritevideos', favs)

####################################################################################################

def FavoriteVideos(sender):
  c = ContextMenu(includeStandardItems=False)
  c.Append(Function(DirectoryItem(RemoveVideoFromFavorites, title='Remove from favorites')))

  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle, noCache=True, contextMenu=c)

  favs = Data.LoadObject('favoritevideos')
  values = favs.values()
  output = [(f[1], f[0], f[2]) for f in values]
  output.sort()

  for name, videoId, summary in output:
    video_page = HTTP.Request(VIDEO_URL % videoId)
    id = re.search('videoconfig\?v=([^%&]+)', video_page).group(1)

    thumb = XML.ElementFromURL(XML_INFO % id, errors='ignore').xpath('/config/image')[0].text
    dir.Append(WebVideoItem(VIDEO_URL % videoId, title=name, summary=summary, thumb=Function(GetThumb, url=thumb), contextKey=videoId, contextArgs={}))
  return dir

####################################################################################################

def GetThumb(url):
  data = HTTP.Request(url, cacheTime=CACHE_1MONTH)
  if data:
    return DataObject(data, 'image/jpeg')
  else:
    return Redirect(R(ICON_DEFAULT))

####################################################################################################

def About(sender):
  return MessageContainer('About (version ' + str(VERSION) + ')', 'This is an unofficial and unsupported plugin to watch videos\nfrom 4tube.com. This plugin is in no way affiliated, endorsed\nor sponsored by 4tube or Plex.')

####################################################################################################

def UpdateAvailable(sender):
  return MessageContainer('Update Available', 'An update for this plugin is availble at\nhttp://bit.ly/4tube4plex')
