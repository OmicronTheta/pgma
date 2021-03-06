# HelixStudios
import re, os, platform, urllib, io, time
from difflib import SequenceMatcher
import xml.etree.ElementTree as xmltree

#Fix HTTPS errors when connecting to Facebox (neural.vigue.me) and Thumbor CDN (cdn.vigue.me)
import certifi
import requests

PLUGIN_LOG_TITLE = 'XML'	# Log Title

VERSION_NO = '2019.03.11.1'

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0
file_name_pattern = re.compile(Prefs['regex'])

def Start():
	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
        'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
        '.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

class XML(Agent.Movies):
	name = 'xmladult'
	languages = [Locale.Language.NoLanguage, Locale.Language.English]
	primary_provider = False
	fallback_agent = ['com.plexapp.agents.gayporncollector']
	contributes_to = ['com.plexapp.agents.cockporn']

	def Log(self, message, *args):
		if Prefs['debug']:
			Log(PLUGIN_LOG_TITLE + ' - ' + message, *args)

	def intTest(self, s):
		try:
			int(s)
			return int(s)
		except ValueError:
			return False

	def similar(self, a, b):
		return SequenceMatcher(None, a, b).ratio()

	def search(self, results, media, lang, manual):
		self.Log('-----------------------------------------------------------------------')
		self.Log('SEARCH CALLED v.%s', VERSION_NO)
		self.Log('SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.Log('SEARCH - media.title - %s', media.title)
		self.Log('SEARCH - media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
		self.Log('SEARCH - media.primary_metadata.title - %s', media.primary_metadata.title)
		self.Log('SEARCH - media.items - %s', media.items)
		self.Log('SEARCH - media.filename - %s', media.filename)
		self.Log('SEARCH - lang - %s', lang)
		self.Log('SEARCH - manual - %s', manual)
		self.Log('SEARCH - Prefs->folders - %s', Prefs['folders'])
		self.Log('SEARCH - Prefs->regex - %s', Prefs['regex'])

		if not media.items[0].parts[0].file:
			return

		path_and_file = media.items[0].parts[0].file
		self.Log('SEARCH - File Path: %s', path_and_file)

		(file_dir, basename) = os.path.split(os.path.splitext(path_and_file)[0])
		final_dir = os.path.split(file_dir)[1]

		self.Log('SEARCH - Enclosing Folder: %s', final_dir)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if final_dir.lower() not in folder_list:
				self.Log('SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', basename, final_dir, ','.join(folder_list))
				return

		m = file_name_pattern.search(basename)
		if not m:
			self.Log('SEARCH - Skipping %s because the file name is not in the expected format.', basename)
			return

		filetitle = path_and_file.split("/")[-1];
		filetitle = filetitle.split(".")[0];
		metadatafile = "/data/media/drive-encrypt/Videos/Videos/XML/metadata/" + filetitle + ".xml";
		Log(metadatafile)
		Log(os.path.exists("/data/media/drive-encrypt/Videos/Videos/XML/" + filetitle + ".xml"))
		self.Log('SEARCH - Found existing metadata');
		results.Append(MetadataSearchResult(id = metadatafile, name = metadatafile, score = 100, lang = lang))
		return

	def update(self, metadata, media, lang, force=False):
		self.Log('UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		metadatafile = metadata.id
		meta = xmltree.parse(metadatafile)
		root = meta.getroot()

		valid_image_names = list()
		valid_art_names = list()

		metadata.title = root.findall("Title")[0].text
		metadata.title = metadata.title.replace("&apos;","'");
		metadata.rating = float(int(root.findall("Rating")[0].text)/10)
		metadata.summary = root.findall("Description")[0].text
		metadata.summary = metadata.summary.replace("&apos;","'");
		metadata.summary = metadata.summary.replace("&amp;","&");
		mov_cover_hires = root.findall("Cover")[0].text
		mov_cover_hires = mov_cover_hires.replace("%26","&");
		if "," in mov_cover_hires:
			mov_covers_hires = mov_cover_hires.split(",")
			for cover in mov_covers_hires:
				if cover != None:
					try:
						valid_image_names.append(cover)
						metadata.posters[cover]=Proxy.Media(HTTP.Request(cover), sort_order = 1)
						metadata.posters.validate_keys(valid_image_names)
					except Exception as e:
						pass
		else:
			valid_image_names.append(mov_cover_hires)
			metadata.posters[mov_cover_hires]=Proxy.Media(HTTP.Request(mov_cover_hires), sort_order = 1)
			metadata.posters.validate_keys(valid_image_names)

		art_url = root.findall("Background")[0].text
		art_url = art_url.replace("%26","&")
		if "," in art_url:
			art_urls = art_url.split(",")
			for art in art_urls:
				if cover != None:
					try:
						valid_art_names.append(art)
						metadata.art[art] = Proxy.Media(HTTP.Request(art), sort_order=1)
						metadata.art.validate_keys(valid_art_names)
					except Exception as e:
						pass
		else:
			valid_art_names.append(art_url)
			metadata.art[art_url] = Proxy.Media(HTTP.Request(art_url), sort_order=1)
			metadata.art.validate_keys(valid_art_names)

		raw_date = root.findall('ReleaseDate')[0].text
		metadata.originally_available_at = Datetime.ParseDate(raw_date).date()
		metadata.year = metadata.originally_available_at.year
		studio = root.findall("Studio")[0].text

		#Cast images
		metadata.roles.clear()

		rolethumbs = list();
		headshot_list = root.findall('Cast/Actor/Photo')
		for headshot in headshot_list:
			headshot_url = headshot.text
			if "freecdn.belamionline.com" not in headshot_url and "freshmen.net" not in headshot_url:
				#Ask facebox to query image for face bounding boxes
				result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url}, verify=certifi.where())
				box = {}
				try:
					box = result.json()["faces"][0]["rect"]
					cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(abs(box["left"] - 50)) + "x" + str(abs(box["top"] - 50)) + ":" + str(abs((box["left"]+box["width"])+50)) + "x" + str(abs((box["top"]+box["height"])+50)) + "/" + headshot_url
					rolethumbs.append(cropped_headshot)
				except Exception as e:
					cropped_headshot = "https://via.placeholder.net/400";
					rolethumbs.append(cropped_headshot)
					pass
			else:
				rolethumbs.append(headshot_url)
		index = 0
		cast_text_list = root.findall('Cast/Actor/Name');
		for castn in cast_text_list:
			Log(rolethumbs[index])
			cast = castn.text
			cname = cast.strip()
			if (len(cname) > 0):
				role = metadata.roles.new()
				role.name = cname
				role.photo = rolethumbs[index]
				role.role = root.findall('Cast/Actor/Role')[index].text
			index += 1

		metadata.collections.add(studio)
		metadata.content_rating = 'X'
		metadata.studio = studio
		return
