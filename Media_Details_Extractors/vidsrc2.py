import base64
import re
import cloudscraper
from urllib.parse import quote, unquote
import time
from utils import VidSrcError, mapp, rc4, reverse, subst, subst_
from Video_Extractors.f2cloud import F2Cloud
from keys import source_keys

class Vidsrc:
    HOST = 'vidsrc2.to'
    keys = source_keys['vidsrc2.to']
    source = 'vid2v11.site'
    scraper = cloudscraper.create_scraper()

    @staticmethod
    def enc(inp):
        a = mapp(subst(rc4(Vidsrc.keys[0], reverse(inp))), Vidsrc.keys[1], Vidsrc.keys[2])
        a = mapp(reverse(subst(rc4(Vidsrc.keys[3], a))), Vidsrc.keys[4], Vidsrc.keys[5])
        a = subst(rc4(Vidsrc.keys[8], reverse(mapp(a, Vidsrc.keys[6], Vidsrc.keys[7]))))
        return subst(a)

    @staticmethod
    def dec(inp):
        a = subst_(inp)
        a = mapp(reverse(rc4(Vidsrc.keys[8], subst_(a))), Vidsrc.keys[7], Vidsrc.keys[6])
        a = rc4(Vidsrc.keys[3], subst_(reverse(mapp(a, Vidsrc.keys[5], Vidsrc.keys[4]))))
        a = reverse(rc4(Vidsrc.keys[0], subst_(mapp(a, Vidsrc.keys[2], Vidsrc.keys[1]))))
        return a

    @staticmethod
    def fetch_streams_and_subtitles(data_id):
        time_millis = hex(int(time.time() * 1000))[2:]
        time_query_params = f"t={quote(time_millis)}&h={quote(Vidsrc.enc(time_millis))}"
        url = f"https://{Vidsrc.HOST}/ajax/embed/episode/{data_id}/sources?token={quote(Vidsrc.enc(data_id))}&{time_query_params}"
        req = Vidsrc.scraper.get(url)

        if req.status_code != 200:
            raise VidSrcError(f"Couldnt fetch {req.url}, status code: {req.status_code}...")

        result = req.json().get('result', [])
        if not result or len(result) < 2:
            raise VidSrcError("Invalid response structure for episode sources")

        f2_cloud_id = result[0]['id']
        filemoon_id = result[1]['id']

        # Fetching F2Cloud stream
        f2cloud_url = Vidsrc.fetch_source_url(f2_cloud_id, time_query_params)
        decrypted_f2cloud_url = Vidsrc.dec(f2cloud_url)

        # Fetching Filemoon embed URL
        filemoon_url = Vidsrc.fetch_source_url(filemoon_id, time_query_params)
        decrypted_filemoon_url = Vidsrc.dec(filemoon_url)

        return {
            'f2cloud': F2Cloud().stream(decrypted_f2cloud_url, Vidsrc.source),
            'filemoon_embed': decrypted_filemoon_url,  # Returning the Filemoon embed URL
        }

    @staticmethod
    def fetch_source_url(source_id, time_query_params):
        url = f"https://{Vidsrc.HOST}/ajax/embed/source/{source_id}?token={quote(Vidsrc.enc(source_id))}&{time_query_params}"
        req = Vidsrc.scraper.get(url)

        if req.status_code != 200:
            raise VidSrcError(f"Couldnt fetch {req.url}, status code: {req.status_code}...")

        return req.json().get('result', {}).get('url')

    def fetch_movie(self, tmdb_id):
        url = f"https://{self.HOST}/embed/movie/{tmdb_id}"
        req = self.scraper.get(url)
        if req.status_code != 200:
            raise VidSrcError(f"Couldnt fetch {req.url}, status code: {req.status_code}...")

        data_id = re.search(r'data-id="(.*?)"', req.text).group(1)
        if not data_id:
            print("[VidSrcExtractor] Could not fetch data-id, this could be due to an invalid imdb/tmdb code...")
            return []

        return self.fetch_streams_and_subtitles(data_id)

    def fetch_tv(self, tmdb_id, season, episode):
        url = f"https://{self.HOST}/embed/tv/{tmdb_id}/{season}/{episode}"
        req = self.scraper.get(url)
        if req.status_code != 200:
            raise VidSrcError(f"Couldnt fetch {req.url}, status code: {req.status_code}...")

        data_id = re.search(r'data-id="(.*?)"', req.text).group(1)
        if not data_id:
            print("[VidSrcExtractor] Could not fetch data-id, this could be due to an invalid imdb/tmdb code...")
            return []

        return self.fetch_streams_and_subtitles(data_id)
