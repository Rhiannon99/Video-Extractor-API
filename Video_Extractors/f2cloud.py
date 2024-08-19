import requests
import re
import json
import cloudscraper
from urllib.parse import urlparse, quote
from keys import source_keys
from utils import VidSrcError
from utils import subst_, subst, rc4, reverse, mapp, general_enc

class F2Cloud:
    @staticmethod
    def h_enc(inp, source):
        return general_enc(source_keys[source][9], inp)

    @staticmethod
    def embed_enc(inp, source):
        keys = source_keys[source]
        a = mapp(subst(rc4(keys[0], inp)), keys[1], keys[2])
        a = subst(rc4(keys[5], mapp(reverse(a), keys[3], keys[4])))
        a = subst(rc4(keys[6], reverse(a)))
        a = subst(reverse(mapp(a, keys[7], keys[8])))
        return a

    @staticmethod
    def embed_dec(inp, source):
        keys = source_keys[source]
        a = subst_(inp)
        a = rc4(keys[6], subst_((a := mapp(reverse(a), keys[8], keys[7]))))
        a = mapp(rc4(keys[5], subst_(reverse(a))), keys[4], keys[3])
        a = rc4(keys[0], subst_(mapp(reverse(a), keys[2], keys[1])))
        return a

    def stream(self, url, source):
        scraper = cloudscraper.create_scraper()
        url = urlparse(url)
        embed_id = url.path.split('/')[2]

        h = self.h_enc(embed_id, source)

        mediainfo_url = f"https://{url.hostname}/mediainfo/{self.embed_enc(embed_id, source)}?{url.query}&ads=0&h={quote(h)}"
        req = scraper.get(mediainfo_url)

        if req.status_code != 200:
            raise VidSrcError(f"Failed! {mediainfo_url} - Status Code: {req.status_code}")

        req = req.json()
        playlist = json.loads(self.embed_dec(req['result'], source))
        sources = playlist.get('sources')

        # Directly return the first source URL without parsing further
        first_source_url = sources[0].get("file")
        
        return {
            "quality": "source",
            "url": first_source_url,
            "is_m3u8": ".m3u8" in first_source_url
        }
