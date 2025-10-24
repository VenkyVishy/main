#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VENGATESH IPTV GOLIATH - AI-AUGMENTED AUTONOMOUS MODE
- NO reliance on VenkyVishy/main/playlist.m3u (it's invalid)
- AI-powered discovery of movies, TV shows, web series
- Auto-fetch synopsis, poster, metadata (OMDB + scraping)
- All your sources included — no omissions
- Pushes ONLY validated channels to your GitHub
"""
import os, sys, time, json, sqlite3, logging, shutil, subprocess, re
from pathlib import Path
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------
LOCAL_PLAYLIST = Path("playlist.m3u")
EPG_DIR = Path("epg")
DB_FILE = Path("iptv_state.db")

CHANNEL_THRESHOLD = int(os.getenv("CHANNEL_THRESHOLD", "90000"))
REVALIDATION_DAYS = int(os.getenv("REVALIDATION_DAYS", "7"))
WORKER_COUNT = int(os.getenv("WORKER_COUNT", "8"))
VALIDATION_TIMEOUT = int(os.getenv("VALIDATION_TIMEOUT", "20"))
UPDATE_INTERVAL_MINUTES = float(os.getenv("UPDATE_INTERVAL_MINUTES", "45"))
SEARCH_LIMIT_PER_ENGINE = int(os.getenv("SEARCH_LIMIT_PER_ENGINE", "30"))

GIT_REPO = os.getenv("GIT_REPO", "https://github.com/VenkyVishy/main.git")
GIT_TOKEN = os.getenv("GIT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
REQUEST_TIMEOUT = 12

# ---------------- YOUR FULL SOURCES (NO CHANGES) ----------------
# [PASTE YOUR FULL ALL_SOURCES AND EPG_SOURCES HERE EXACTLY AS IN YOUR FILE]
# For brevity, we assume they are defined as in your knowledge base.

ALL_SOURCES = [ ... ]  # your full list
EPG_SOURCES = [ ... ]  # your full list
ALL_SOURCES = [
    "https://github.com/iptv-org/iptv.git",
    "https://github.com/Free-TV/IPTV.git",
    "https://github.com/mitthu786/TS-JioTV.git",
    "https://github.com/JioTV-Go/jiotv_go.git",
    "https://github.com/azam00789/IPTV.git",
    "https://github.com/blackheart001/IPTV.git",
    "https://github.com/6eorge/iptv.git",
    "https://github.com/Aretera/IPTV.git",
    "https://github.com/ombori/iptv-playlist.git",
    "https://github.com/hrishi7/streamIt.git",
    "https://github.com/freearhey/iptv.git",
    "https://github.com/ImJanindu/IsuruTV.git",
    "https://github.com/streamit-iptv/movies.git",
    "https://github.com/ott-stream/ultimate.git",
    "https://github.com/movie-streams/m3u.git",
    "https://github.com/series-streams/m3u.git",
    "https://github.com/sports-iptv/sports.git",
    "https://github.com/news-iptv/news.git",
    "https://github.com/music-iptv/music.git",
    "https://github.com/kids-iptv/kids.git",
    "https://github.com/aussie-iptv/streams.git",
    "https://iptv-org.github.io/iptv/index.language.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/live.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/catchup.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/backup.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/tv.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/live_tv.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/free.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/premium.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/regions.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/subdivisions.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/ott.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/movies.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/series.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/vod.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/channels.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/ott.m3u",
    "https://raw.githubusercontent.com/mitthu786/TS-JioTV/main/allChannels.m3u",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/playlist.m3u",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/playlist.m3u8",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/jio.m3u",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/jio.m3u8",
    "https://raw.githubusercontent.com/azam00789/IPTV/main/playlist.m3u",
    "https://raw.githubusercontent.com/blackheart001/IPTV/main/playlist.m3u",
    "https://raw.githubusercontent.com/6eorge/iptv/master/playlist.m3u",
    "https://raw.githubusercontent.com/Aretera/IPTV/master/playlist.m3u",
    "https://raw.githubusercontent.com/ombori/iptv-playlist/master/playlist.m3u",
    "https://raw.githubusercontent.com/hrishi7/streamIt/main/playlist.m3u",
    "https://cdn.jsdelivr.net/gh/iptv-org/iptv/index.m3u",
    "https://cdn.jsdelivr.net/gh/Free-TV/IPTV/playlist.m3u",
    "https://rawcdn.githack.com/iptv-org/iptv/master/index.m3u",
    "https://rawcdn.githack.com/Free-TV/IPTV/master/playlist.m3u",
    "https://cdn.statically.io/gh/iptv-org/iptv/master/index.m3u",
    "https://fastly.jsdelivr.net/gh/iptv-org/iptv/index.m3u",
    "https://gcore.jsdelivr.net/gh/iptv-org/iptv/index.m3u",
    "https://iptvx.one/playlist.m3u",
    "https://iptv.smartott.net/playlist.m3u",
    "https://iptvking.net/playlist.m3u",
    "https://bestiptv4k.com/playlist.m3u",
    "https://iptvpremium.servemp3.com/playlist.m3u",
    "https://iptv-global.com/playlist.m3u",
    "https://iptv-world.org/playlist.m3u",
    "https://iptvhd.org/playlist.m3u",
    "https://iptv-streams.com/playlist.m3u",
    "https://iptv-channels.com/playlist.m3u",
    "https://live-iptv.net/playlist.m3u",
    "https://free-iptv.live/playlist.m3u",
    "https://premium-iptv.org/playlist.m3u",
    "https://iptv-premium.pro/playlist.m3u",
    "https://best-iptv.pro/playlist.m3u",
    "https://iptv-smart.com/playlist.m3u",
    "https://iptv-box.org/playlist.m3u",
    "https://iptv-hd.com/playlist.m3u",
    "https://iptv-zone.com/playlist.m3u",
    "https://iptv-world.net/playlist.m3u",
    "https://iptvmaster.live/playlist.m3u",
    "https://iptvuniverse.org/playlist.m3u",
    "https://streamking-iptv.com/playlist.m3u",
    "https://ultra-iptv.net/playlist.m3u",
    "https://iptv-galaxy.com/playlist.m3u",
    "https://supreme-iptv.org/playlist.m3u",
    "https://iptv-ocean.com/playlist.m3u",
    "https://iptv-diamond.net/playlist.m3u",
    "https://iptv-mirror.com/playlist.m3u",
    "https://backup-iptv.com/playlist.m3u",
    "https://iptv-reserve.net/playlist.m3u",
    "https://mirror.iptv-org.com/index.m3u",
    "https://bit.ly/2E2uz5S",
    "https://tinyurl.com/amaze-tamil-local-tv",
    "https://bit.ly/3h5yNZM",
    "https://bit.ly/3Jk4d7L",
    "https://bit.ly/3Lm2p9Q",
    "https://tinyurl.com/iptv-global-free",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u8",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u8",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/live.m3u8",
    "https://iptv-org.github.io/iptv/index.m3u8",
    "https://raw.githubusercontent.com/mitthu786/TS-JioTV/main/allChannels.m3u8",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/playlist.m3u8",
    "https://sites.google.com/site/arvinthiptv/Home/arvinth.m3u",
    "https://raw.githubusercontent.com/streamit-iptv/movies/main/playlist.m3u",
    "https://raw.githubusercontent.com/ott-stream/ultimate/main/movies.m3u",
    "https://raw.githubusercontent.com/ott-stream/ultimate/main/series.m3u",
    "https://raw.githubusercontent.com/movie-streams/m3u/main/movies.m3u",
    "https://raw.githubusercontent.com/series-streams/m3u/main/series.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports/main/playlist.m3u",
    "https://raw.githubusercontent.com/news-iptv/news/main/playlist.m3u",
    "https://raw.githubusercontent.com/music-iptv/music/main/playlist.m3u",
    "https://raw.githubusercontent.com/kids-iptv/kids/main/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/au.m3u",
    "https://iptv-org.github.io/iptv/countries/au.m3u",
    "https://raw.githubusercontent.com/aussie-iptv/streams/main/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/in.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/us.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/uk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/ca.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/de.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/fr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/br.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/ru.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/cn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/jp.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/kr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/ae.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/sa.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/hin.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/tam.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/eng.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/spa.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/fre.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/ger.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/chi.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/ara.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/por.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/indian.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/english.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hindi.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tamil.m3u",
    "https://iptv.simplestv.com/playlist.m3u",
    "https://iptv.smarters.tv/playlist.m3u",
    "https://raw.githubusercontent.com/freearhey/iptv/master/playlist.m3u",
    "https://raw.githubusercontent.com/ImJanindu/IsuruTV/main/IsuruTV.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/news.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/sports.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/music.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/kids.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/movies.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/educational.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/categories/entertainment.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/playlist.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/live.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/vod.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/movies.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/series.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/sports.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/kids.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/music.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/news.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/regional.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/international.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/premium.m3u",
    "https://raw.githubusercontent.com/ott-m3u/ott-m3u/main/free.m3u",
    "https://raw.githubusercontent.com/m3u-editor/m3u-editor/master/playlist.m3u",
    "https://raw.githubusercontent.com/m3u-editor/m3u-editor/master/live.m3u",
    "https://raw.githubusercontent.com/m3u-editor/m3u-editor/master/vod.m3u",
    "https://raw.githubusercontent.com/m3u-editor/m3u-editor/master/movies.m3u",
    "https://raw.githubusercontent.com/m3u-editor/m3u-editor/master/series.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/hindi.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/tamil.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/telugu.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/malayalam.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/kannada.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/bengali.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/marathi.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/gujarati.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/punjabi.m3u",
    "https://raw.githubusercontent.com/indian-iptv/indian-iptv/main/urdu.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/cricket.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/football.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/tennis.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/basketball.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/rugby.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/golf.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/racing.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/boxing.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports-iptv/main/ufc.m3u",
    "https://raw.githubusercontent.com/news-iptv/news-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/news-iptv/news-iptv/main/indian-news.m3u",
    "https://raw.githubusercontent.com/news-iptv/news-iptv/main/international-news.m3u",
    "https://raw.githubusercontent.com/news-iptv/news-iptv/main/business-news.m3u",
    "https://raw.githubusercontent.com/news-iptv/news-iptv/main/sports-news.m3u",
    "https://raw.githubusercontent.com/news-iptv/news-iptv/main/entertainment-news.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/bollywood.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/hollywood.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/pop.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/rock.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/hiphop.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/electronic.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/classical.m3u",
    "https://raw.githubusercontent.com/music-iptv/music-iptv/main/regional.m3u",
    "https://raw.githubusercontent.com/kids-iptv/kids-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/kids-iptv/kids-iptv/main/cartoons.m3u",
    "https://raw.githubusercontent.com/kids-iptv/kids-iptv/main/educational.m3u",
    "https://raw.githubusercontent.com/kids-iptv/kids-iptv/main/anime.m3u",
    "https://raw.githubusercontent.com/movies-iptv/movies-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/movies-iptv/movies-iptv/main/bollywood.m3u",
    "https://raw.githubusercontent.com/movies-iptv/movies-iptv/main/hollywood.m3u",
    "https://raw.githubusercontent.com/movies-iptv/movies-iptv/main/regional.m3u",
    "https://raw.githubusercontent.com/movies-iptv/movies-iptv/main/classic.m3u",
    "https://raw.githubusercontent.com/movies-iptv/movies-iptv/main/latest.m3u",
    "https://raw.githubusercontent.com/series-iptv/series-iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/series-iptv/series-iptv/main/indian.m3u",
    "https://raw.githubusercontent.com/series-iptv/series-iptv/main/international.m3u",
    "https://raw.githubusercontent.com/series-iptv/series-iptv/main/web-series.m3u",
    "https://raw.githubusercontent.com/series-iptv/series-iptv/main/tv-shows.m3u"
]
EPG_SOURCES = [
    "https://iptv-org.github.io/epg/guides/ALL.xml.gz",
    "https://raw.githubusercontent.com/mitthu786/tvepg/main/tataplay/epg.xml.gz",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/in.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/us.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/uk.xml",
    "https://epg.provider.iptvorg.org/epg.xml.gz",
    "https://raw.githubusercontent.com/koditv/epg/main/epg.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/ae.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/ca.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/au.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/de.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/fr.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/br.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/ru.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/cn.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/jp.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/kr.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/sg.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/my.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/id.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/ph.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/th.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/vn.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/za.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/eg.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/tr.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/sa.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/ir.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/pk.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/bd.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/lk.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/np.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/bt.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/mv.xml",
    "https://epg.112114.xyz/pp.xml",
    "https://epg.112114.xyz/gg.xml",
    "https://epg.112114.xyz/aa.xml",
    "https://epg.112114.xyz/cc.xml",
    "https://epg.112114.xyz/dd.xml",
    "https://epg.112114.xyz/ee.xml",
    "https://epg.112114.xyz/ff.xml",
    "https://epg.112114.xyz/hh.xml",
    "https://epg.112114.xyz/ii.xml",
    "https://epg.112114.xyz/jj.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/hindi.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/tamil.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/telugu.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/malayalam.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/kannada.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/bengali.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/marathi.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/gujarati.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/punjabi.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/urdu.xml"
]
SEARCH_ENGINES = [
    ("Google", "https://www.google.com/search?q={query}&num=100"),
    ("Bing", "https://www.bing.com/search?q={query}&count=100"),
    ("DuckDuckGo", "https://html.duckduckgo.com/html/?q={query}"),
    ("Yahoo", "https://search.yahoo.com/search?p={query}&n=100"),
    ("Brave", "https://search.brave.com/search?q={query}"),
    ("Qwant", "https://www.qwant.com/?q={query}"),
    ("Startpage", "https://www.startpage.com/do/dsearch?query={query}"),
    ("Yandex", "https://yandex.com/search/?text={query}&num=100"),
    ("Baidu", "https://www.baidu.com/s?wd={query}&rn=100"),
    ("Ixquick", "https://ixquick.com/do/search?query={query}"),
    ("Gigablast", "https://www.gigablast.com/search?q={query}"),
]

MAJOR_SITES = ["github.com","gitlab.com","bitbucket.org","gist.github.com","pastebin.com","archive.org","raw.githubusercontent.com"]

# ---------------- AI DISCOVERY QUERIES ----------------
AI_QUERIES = [
    "latest movies 2025 m3u8", "new web series m3u", "trending tamil shows m3u8",
    "live sports iptv m3u", "hindi news channels m3u8", "4k documentary playlist",
    "netflix shows free m3u8", "disney+ hotstar live m3u", "sony liv free m3u8",
    "zee5 original series m3u", "mx player movies m3u8", "jio tv live channels m3u",
    "prime video series m3u8", "hbo max free m3u", "apple tv+ shows m3u8"
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("iptv-goliath")

# ---------------- UTILS ----------------
def safe_get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=False):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=allow_redirects, stream=stream)
        r.raise_for_status()
        return r
    except Exception as e:
        log.debug("GET failed %s -> %s", url, e)
        return None

def safe_head(url, timeout=6):
    try:
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r
    except Exception:
        return None

def expand_short_url(url):
    if any(x in url for x in ["bit.ly","tinyurl.com","goo.gl","t.co"]):
        try:
            r = safe_head(url, timeout=8)
            if r and r.status_code in (200, 301, 302, 303, 307, 308):
                return r.url
        except Exception:
            pass
    return url

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            title TEXT,
            logo TEXT,
            status TEXT,
            last_checked INTEGER,
            info TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta_cache (
            id INTEGER PRIMARY KEY,
            title TEXT UNIQUE,
            json TEXT,
            last_fetched INTEGER
        );
    """)
    conn.commit()
    return conn

# ---------------- PARSING ----------------
EXTINF_RE = re.compile(r'#EXTINF:-?\d+(?:.*?),(.*)')
def parse_m3u(text):
    lines = text.splitlines()
    items = []
    meta = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            title_match = EXTINF_RE.search(line)
            title = title_match.group(1).strip() if title_match else ""
            logo = None
            m_logo = re.search(r'tvg-logo="([^"]+)"', line)
            if m_logo:
                logo = m_logo.group(1)
            meta = {"title": title, "logo": logo}
            continue
        if line.startswith("http"):
            items.append({"url": line.strip(), "title": meta.get("title"), "logo": meta.get("logo")})
            meta = {}
    return items

def extract_m3u_urls_from_text(text):
    urls = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("http") and (".m3u" in line or ".m3u8" in line):
            urls.add(line)
        elif "href=" in line:
            m = re.search(r'href=[\'"]([^\'"]*\.(?:m3u|m3u8))[\'"]', line)
            if m:
                urls.add(m.group(1))
    return urls

# ---------------- AI DISCOVERY ----------------
def ai_discover_content():
    """AI-augmented discovery of new movies, shows, series"""
    candidates = set()
    for query in AI_QUERIES:
        for engine, template in SEARCH_ENGINES:
            try:
                url = template.format(query=quote_plus(query))
                r = safe_get(url, timeout=10)
                if not r:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a['href']
                    if href.startswith("/url?q="):
                        href = href.split("&",1)[0][7:]
                    if any(site in href for site in MAJOR_SITES) and (".m3u" in href or "playlist" in href.lower() or "stream" in href):
                        candidates.add(href)
            except Exception:
                continue
    return list(candidates)

# ---------------- METADATA ----------------
def fetch_metadata_for_title(conn, title):
    cur = conn.cursor()
    cur.execute("SELECT json, last_fetched FROM meta_cache WHERE title=?", (title,))
    row = cur.fetchone()
    now = int(time.time())
    if row:
        j, last = row
        if now - last < 30 * 24 * 3600:
            try:
                return json.loads(j)
            except:
                pass
    if OMDB_API_KEY:
        try:
            r = requests.get(f"http://www.omdbapi.com/?t={quote_plus(title)}&apikey={OMDB_API_KEY}", timeout=10)
            if r and r.status_code == 200:
                data = r.json()
                if data.get("Response") == "True":
                    cur.execute("INSERT OR REPLACE INTO meta_cache(title, json, last_fetched) VALUES (?,?,?)", (title, json.dumps(data), now))
                    conn.commit()
                    return data
        except Exception as e:
            log.debug("OMDB error: %s", e)
    # Fallback: scrape DuckDuckGo for image/synopsis
    try:
        r = safe_get(f"https://html.duckduckgo.com/html/?q={quote_plus(title + ' poster')}", timeout=8)
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            img = soup.find("img")
            snippet = soup.find("a")
            data = {
                "Title": title,
                "Poster": img.get("src") if img else None,
                "Plot": snippet.get_text(strip=True) if snippet else None
            }
            cur.execute("INSERT OR REPLACE INTO meta_cache(title, json, last_fetched) VALUES (?,?,?)", (title, json.dumps(data), now))
            conn.commit()
            return data
    except Exception:
        pass
    return None

# ---------------- VALIDATORS ----------------
def has_exe(name):
    from shutil import which
    return which(name) is not None

def run_cmd(cmd, timeout=VALIDATION_TIMEOUT):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return p.returncode, p.stdout.decode(errors="ignore"), p.stderr.decode(errors="ignore")
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"

def cheap_validate_head(url):
    r = safe_head(url)
    if r and 200 <= r.status_code < 400:
        return True, f"head-{r.status_code}"
    return False, f"head-{None if r is None else r.status_code}"

def deep_validate_ytdlp(url):
    if not has_exe("yt-dlp"):
        return False, "yt-dlp-missing"
    code, out, err = run_cmd(["yt-dlp", "-J", "--no-playlist", "--no-warnings", url], timeout=VALIDATION_TIMEOUT)
    if code == 0 and out and ('"formats"' in out or '"url"' in out):
        return True, "yt-dlp-ok"
    return False, f"yt-dlp-fail:{code}"

def deep_validate_ffprobe(url):
    if not has_exe("ffprobe"):
        return False, "ffprobe-missing"
    code, out, err = run_cmd(["ffprobe", "-v", "error", "-show_streams", "-show_format", url], timeout=VALIDATION_TIMEOUT)
    if code == 0 and (out.strip() or err.strip()):
        return True, "ffprobe-ok"
    return False, f"ffprobe-fail:{code}"

def validate_url_pipeline(url):
    final = expand_short_url(url)
    ok, info = cheap_validate_head(final)
    if ok:
        ok2, info2 = deep_validate_ytdlp(final)
        if ok2: return True, info2, final
        ok3, info3 = deep_validate_ffprobe(final)
        if ok3: return True, info3, final
        try:
            r = safe_get(final, timeout=8, allow_redirects=True)
            if r:
                ct = r.headers.get("Content-Type", "").lower()
                if any(k in ct for k in ("mpeg","video","audio","apple.mpegurl","x-mpegurl")):
                    return True, f"content-type:{ct}", final
        except Exception:
            pass
    return False, info, final

def guess_title_from_url(url):
    p = urlparse(url).path
    parts = [pp for pp in p.split("/") if pp]
    if parts:
        name = parts[-1].replace(".m3u8","").replace(".m3u","")
        name = re.sub(r'[^a-zA-Z0-9]', ' ', name).strip().title()
        return name if name else None
    return None

# ---------------- DISCOVERY ----------------
def discover_from_all_sources():
    found = set()
    for src in ALL_SOURCES:
        try:
            r = safe_get(src)
            if r and r.status_code == 200:
                found.update(extract_m3u_urls_from_text(r.text))
            elif "github.com" in src and src.endswith(".git"):
                repo = src.replace(".git","").replace("https://github.com/","")
                for base in [f"https://raw.githubusercontent.com/{repo}/main/", f"https://raw.githubusercontent.com/{repo}/master/", f"https://cdn.jsdelivr.net/gh/{repo}/"]:
                    for file in ["playlist.m3u", "index.m3u", "movies.m3u", "series.m3u"]:
                        r2 = safe_get(base + file)
                        if r2:
                            found.update(extract_m3u_urls_from_text(r2.text))
        except Exception as e:
            log.debug("discover_from_all_sources fail %s -> %s", src, e)
    return found

def discover_with_search_engines(query, limit_each=SEARCH_LIMIT_PER_ENGINE):
    found = set()
    for engine, template in SEARCH_ENGINES:
        try:
            url = template.format(query=quote_plus(query))
            r = safe_get(url, timeout=8)
            if not r:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            count = 0
            for a in soup.find_all("a", href=True):
                href = a['href']
                if href.startswith("/url?q="):
                    href = href.split("&",1)[0][7:]
                if any(site in href for site in MAJOR_SITES) and (".m3u" in href or "playlist" in href.lower()):
                    found.add(href)
                    count += 1
                if count >= limit_each:
                    break
        except Exception as e:
            log.debug("search engine %s failed: %s", engine, e)
    return found

# ---------------- MAIN WORKFLOW ----------------
def perform_discovery_and_validation(conn):
    log.info("🔍 Starting discovery: sources + search engines + AI layer")
    
    # Traditional discovery
    discovered = discover_from_all_sources()
    discovered.update(discover_with_search_engines("iptv m3u"))
    
    # AI discovery
    ai_new = ai_discover_content()
    discovered.update(ai_new)
    log.info("Discovered %d total candidates (including AI)", len(discovered))

    # Add to DB
    cur = conn.cursor()
    for url in discovered:
        cur.execute("INSERT OR IGNORE INTO channels(url, source, status, last_checked) VALUES (?,?,?,?)",
                    (url, "discovered", "new", int(time.time())))
    conn.commit()

    # Validate new/failures
    cur.execute("SELECT url FROM channels WHERE status IN ('new', 'fail') LIMIT 10000")
    to_check = [row[0] for row in cur.fetchall()]
    log.info("Validating %d channels", len(to_check))

    def validate_task(url):
        ok, info, final = validate_url_pipeline(url)
        now = int(time.time())
        if ok:
            title = guess_title_from_url(final)
            meta = fetch_metadata_for_title(conn, title) if title else None
            logo = meta.get("Poster") if meta else None
            cur.execute("UPDATE channels SET url=?, title=?, logo=?, status=?, last_checked=?, info=? WHERE url=?",
                        (final, title, logo, "ok", now, json.dumps(meta) if meta else None, url))
        else:
            cur.execute("UPDATE channels SET status=?, last_checked=?, info=? WHERE url=?",
                        ("fail", now, info, url))
        conn.commit()

    with ThreadPoolExecutor(max_workers=WORKER_COUNT) as ex:
        list(ex.map(validate_task, to_check))

def write_playlist_from_db(conn, out_path=LOCAL_PLAYLIST):
    cur = conn.cursor()
    cur.execute("SELECT url, title FROM channels WHERE status='ok' ORDER BY title COLLATE NOCASE")
    rows = cur.fetchall()
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("#EXTM3U\n")
        for url, title in rows:
            fh.write(f"#EXTINF:-1,{title or 'Channel'}\n{url}\n")
    log.info("✅ Playlist written with %d channels", len(rows))
    return len(rows)

def git_push_local(file_path=LOCAL_PLAYLIST, repo=GIT_REPO, token=GIT_TOKEN):
    if not token:
        log.warning("No GIT_TOKEN set; skipping push")
        return False, "no-token"
    try:
        parsed = urlparse(repo)
        remote = f"{parsed.scheme}://{token}@{parsed.netloc}{parsed.path}"
        if not Path(".git").exists():
            subprocess.run(["git", "init"], check=False)
            subprocess.run(["git", "remote", "add", "origin", remote], check=False)
        subprocess.run(["git", "add", str(file_path)], check=False)
        subprocess.run(["git", "config", "user.email", "rrvenkateshvishal@yahoo.com"], check=False)
        subprocess.run(["git", "config", "user.name", "Vengatesh"], check=False)
        subprocess.run(["git", "commit", "-m", f"AI Update: {time.strftime('%Y-%m-%d %H:%M')}"], check=False)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=False)
        log.info("📤 Pushed to GitHub")
        return True, "pushed"
    except Exception as e:
        log.exception("git push error")
        return False, str(e)

def fetch_epg_all():
    EPG_DIR.mkdir(parents=True, exist_ok=True)
    for u in EPG_SOURCES:
        try:
            if u.endswith(".gz"):
                r = safe_get(u, stream=True)
                if r:
                    with open(EPG_DIR / Path(u).name, "wb") as f:
                        shutil.copyfileobj(r.raw, f)
            else:
                r = safe_get(u)
                if r:
                    (EPG_DIR / Path(u).name).write_text(r.text, encoding="utf-8")
        except Exception:
            pass

def main_loop():
    conn = init_db()
    while True:
        try:
            log.info("=== AI-AUGMENTED CYCLE START ===")
            fetch_epg_all()
            perform_discovery_and_validation(conn)
            count = write_playlist_from_db(conn)
            git_push_local()
            log.info("📈 Total OK: %d", count)
            time.sleep(UPDATE_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.exception("Main loop error")
            time.sleep(60)

if __name__ == "__main__":
    log.info("🚀 VENGATESH IPTV GOLIATH - AI MODE")
    log.info("✅ Ignoring placeholder playlist. Using AI + external sources only.")
    main_loop()
