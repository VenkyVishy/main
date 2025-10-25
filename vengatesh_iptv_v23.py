#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time, json, sqlite3, logging, shutil, subprocess, re, tempfile
from pathlib import Path
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

LOCAL_PLAYLIST = Path("playlist.m3u")
GIT_REPO = "https://github.com/VenkyVishy/main.git"
GIT_FILENAME = "playlist.m3u"
EPG_DIR = Path("epg")
DB_FILE = Path("iptv_state.db")
WORKER_COUNT = 8
UPDATE_INTERVAL_MINUTES = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
REQUEST_TIMEOUT = 12

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

MAJOR_SITES = ["github.com", "gitlab.com", "bitbucket.org", "gist.github.com", "pastebin.com", "archive.org", "raw.githubusercontent.com"]
AI_QUERIES = [
    "latest movies 2025 m3u8", "new web series m3u", "trending tamil shows m3u8",
    "live sports iptv m3u", "hindi news channels m3u8", "4k documentary playlist",
    "netflix shows free m3u8", "disney+ hotstar live m3u", "sony liv free m3u8",
    "zee5 original series m3u", "mx player movies m3u8", "jio tv live channels m3u"
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("iptv-goliath")
WRITTEN_CHANNELS = set()

def safe_get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=False):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=allow_redirects, stream=stream)
        r.raise_for_status()
        return r
    except Exception as e:
        log.debug("GET failed %s -> %s", url, e)
        return None

def expand_short_url(url):
    if any(x in url for x in ["bit.ly", "tinyurl.com", "goo.gl", "t.co"]):
        try:
            r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
            if r and r.status_code in (200, 301, 302, 303, 307, 308):
                return r.url
        except Exception:
            pass
    return url

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
            except Exception:
                pass
    try:
        r = safe_get(f"https://html.duckduckgo.com/html/?q={quote_plus(title + ' poster')}", timeout=8)
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            img = soup.find("img")
            snippet = soup.find("a")
            data = {"Title": title, "Poster": img.get("src") if img else None, "Plot": snippet.get_text(strip=True) if snippet else None}
            cur.execute("INSERT OR REPLACE INTO meta_cache(title, json, last_fetched) VALUES (?,?,?)", (title, json.dumps(data), now))
            conn.commit()
            return data
    except Exception as e:
        log.debug("Web fallback error: %s", e)
    return None

def validate_url_pipeline(url):
    final = expand_short_url(url)
    try:
        r = requests.head(final, headers=HEADERS, timeout=8, allow_redirects=True)
        if r and 200 <= r.status_code < 400:
            ct = (r.headers.get("Content-Type") or "").lower()
            if any(k in ct for k in ("mpeg", "video", "audio", "apple.mpegurl", "x-mpegurl", "octet-stream")):
                return True, f"head-{r.status_code}", final
        r2 = requests.get(final, headers=HEADERS, timeout=8, stream=True)
        if r2 and r2.status_code == 200:
            ct = (r2.headers.get("Content-Type") or "").lower()
            if any(k in ct for k in ("mpeg", "video", "audio", "apple.mpegurl", "x-mpegurl")):
                return True, "get-ok", final
    except Exception:
        pass
    return False, "fail", final

def guess_title_from_url(url):
    p = urlparse(url).path
    parts = [pp for pp in p.split("/") if pp]
    if parts:
        name = parts[-1].replace(".m3u8", "").replace(".m3u", "")
        name = re.sub(r'[^a-zA-Z0-9]', ' ', name).strip().title()
        return name if name else None
    return None

def discover_from_all_sources():
    found = set()
    for src in ALL_SOURCES:
        try:
            r = safe_get(src)
            if r and r.status_code == 200 and r.text:
                found.update(extract_m3u_urls_from_text(r.text))
            elif "github.com" in src and src.endswith(".git"):
                repo = src.replace(".git", "").replace("https://github.com/", "")
                for base in [f"https://raw.githubusercontent.com/{repo}/main/", f"https://raw.githubusercontent.com/{repo}/master/", f"https://cdn.jsdelivr.net/gh/{repo}/"]:
                    for file in ["playlist.m3u", "index.m3u", "movies.m3u", "series.m3u", "playlist.m3u8", "index.m3u8"]:
                        r2 = safe_get(base + file)
                        if r2 and r2.text:
                            found.update(extract_m3u_urls_from_text(r2.text))
        except Exception as e:
            log.debug("discover_from_all_sources fail %s -> %s", src, e)
    return found

def discover_with_search_engines(query, limit_each=30):
    found = set()
    for engine, template in SEARCH_ENGINES:
        try:
            url = template.format(query=quote_plus(query))
            r = safe_get(url, timeout=8)
            if not r: continue
            soup = BeautifulSoup(r.text, "html.parser")
            count = 0
            for a in soup.find_all("a", href=True):
                href = a['href']
                if href.startswith("/url?q="): href = href.split("&", 1)[0][7:]
                if any(site in href for site in MAJOR_SITES) and (".m3u" in href or "playlist" in href.lower() or ".m3u8" in href):
                    found.add(href)
                    count += 1
                if count >= limit_each: break
        except Exception as e:
            log.debug("search engine %s failed: %s", engine, e)
    return found

def ai_discover_content():
    candidates = set()
    for query in AI_QUERIES:
        for engine, template in SEARCH_ENGINES:
            try:
                url = template.format(query=quote_plus(query))
                r = safe_get(url, timeout=10)
                if not r: continue
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a['href']
                    if href.startswith("/url?q="): href = href.split("&", 1)[0][7:]
                    if any(site in href for site in MAJOR_SITES) and (".m3u" in href or "playlist" in href.lower() or "stream" in href):
                        candidates.add(href)
            except Exception:
                continue
    return list(candidates)

def ensure_playlist_header(path=LOCAL_PLAYLIST):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
    else:
        with open(path, "r+", encoding="utf-8") as f:
            content = f.read()
            if not content.startswith("#EXTM3U"):
                f.seek(0, 0)
                f.write("#EXTM3U\n" + content)

def append_to_playlist(url, title=None, logo=None, path=LOCAL_PLAYLIST):
    global WRITTEN_CHANNELS
    if url in WRITTEN_CHANNELS: return False
    with open(path, "a", encoding="utf-8") as f:
        if title or logo:
            attrs = []
            if logo: attrs.append(f'tvg-logo="{logo}"')
            attr_str = " ".join(attrs)
            if attr_str:
                f.write(f'#EXTINF:-1 {attr_str},{title or url}\n{url}\n')
            else:
                f.write(f'#EXTINF:-1,{title or url}\n{url}\n')
        else:
            f.write(f'{url}\n')
    WRITTEN_CHANNELS.add(url)
    log.info("✅ ADDED to playlist: %s", title or url[:50])
    return True

def validate_and_maybe_replace(conn, url, title):
    global WRITTEN_CHANNELS
    cur = conn.cursor()
    ok, info, final = validate_url_pipeline(url)
    now = int(time.time())
    if ok:
        cur.execute("UPDATE channels SET status=?, last_checked=?, info=? WHERE url=?", ("ok", now, info, url))
        conn.commit()
        if not title:
            cur.execute("SELECT title FROM channels WHERE url=?", (url,))
            t = cur.fetchone()
            if not t or not t[0]:
                maybe_title = guess_title_from_url(url)
                if maybe_title:
                    cur.execute("UPDATE channels SET title=? WHERE url=?", (maybe_title, url))
                    conn.commit()
                    title = maybe_title
        logo = None
        if title:
            meta = fetch_metadata_for_title(conn, title)
            if meta:
                logo = meta.get("Poster") or meta.get("poster") or None
        append_to_playlist(final, title, logo)
    else:
        log.debug("❌ Validation failed: %s", url[:200])
        cur.execute("SELECT title FROM channels WHERE url=?", (url,))
        row = cur.fetchone()
        channel_title = (row[0] if row and row[0] else title)
        found_repl = False
        if channel_title:
            candidates = []
            for src in ALL_SOURCES:
                try:
                    r = safe_get(src, timeout=8)
                    if r and r.text and channel_title.lower() in r.text.lower():
                        candidates.extend(extract_m3u_urls_from_text(r.text))
                except Exception:
                    pass
            q = f'"{channel_title}" m3u playlist'
            candidates.extend(discover_with_search_engines(q))
            for cand in candidates:
                if cand in WRITTEN_CHANNELS: continue
                ok2, info2, final2 = validate_url_pipeline(cand)
                if ok2:
                    cur.execute("UPDATE channels SET status=?, last_checked=?, info=? WHERE url=?", ("fail", now, info, url))
                    cur.execute("INSERT INTO channels(url, title, logo, status, last_checked, info) VALUES (?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET status=excluded.status, last_checked=excluded.last_checked, info=excluded.info", (final2, channel_title, None, "ok", now, info2))
                    conn.commit()
                    logo = None
                    meta = fetch_metadata_for_title(conn, channel_title)
                    if meta: logo = meta.get("Poster") or meta.get("poster")
                    append_to_playlist(final2, channel_title, logo)
                    found_repl = True
                    log.info("🔄 Replaced: %s ➡ %s", url[:60], final2[:60])
                    break
        if not found_repl:
            cur.execute("UPDATE channels SET status=?, last_checked=?, info=? WHERE url=?", ("fail", now, info, url))
            conn.commit()

def load_existing_playlist_channels(path=LOCAL_PLAYLIST):
    global WRITTEN_CHANNELS
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("http"):
                    WRITTEN_CHANNELS.add(line)
    log.info("Initialized WRITTEN_CHANNELS with %d existing URLs", len(WRITTEN_CHANNELS))

def fetch_epg_all():
    EPG_DIR.mkdir(parents=True, exist_ok=True)
    for u in EPG_SOURCES:
        try:
            if u.endswith(".gz"):
                r = safe_get(u, stream=True)
                if r:
                    dest = EPG_DIR / Path(u).name
                    with open(dest, "wb") as f:
                        shutil.copyfileobj(r.raw, f)
            else:
                r = safe_get(u)
                if r and r.text:
                    dest = EPG_DIR / Path(u).name
                    dest.write_text(r.text, encoding="utf-8")
        except Exception:
            pass

def git_push_local():
    try:
        subprocess.run(["git", "add", str(LOCAL_PLAYLIST)], check=False)
        subprocess.run(["git", "config", "user.email", "rrvenkateshvishal@yahoo.com"], check=False)
        subprocess.run(["git", "config", "user.name", "Vengatesh"], check=False)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip():
            subprocess.run(["git", "commit", "-m", f"AI Update: {time.strftime('%Y-%m-%d %H:%M:%S')}"], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=False)
            log.info("📤 Pushed to GitHub")
    except Exception as e:
        log.debug("Git push error (ok if repo not initialized): %s", e)

def perform_discovery_and_validation(conn):
    log.info("🔍 Starting discovery: sources + search engines + AI layer")
    discovered = discover_from_all_sources()
    discovered.update(discover_with_search_engines("iptv m3u"))
    ai_new = ai_discover_content()
    discovered.update(ai_new)
    log.info("Discovered %d total candidates", len(discovered))
    cur = conn.cursor()
    for url in discovered:
        try:
            cur.execute("INSERT OR IGNORE INTO channels(url, status, last_checked) VALUES (?,?,?)", (url, "new", int(time.time())))
        except Exception:
            pass
    conn.commit()
    cur.execute("SELECT url, title FROM channels WHERE status IN ('new', 'fail') LIMIT 10000")
    to_check = cur.fetchall()
    log.info("Validating %d channels", len(to_check))
    with ThreadPoolExecutor(max_workers=WORKER_COUNT) as ex:
        futures = {ex.submit(validate_and_maybe_replace, conn, url, title): (url, title) for url, title in to_check}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                log.debug("Validation task failed: %s", e)

def main_loop():
    ensure_playlist_header()
    load_existing_playlist_channels()
    conn = init_db()
    cycle = 0
    while True:
        try:
            cycle += 1
            log.info("=== AI-REAL-TIME CYCLE START (%d) ===", cycle)
            fetch_epg_all()
            perform_discovery_and_validation(conn)
            cur = conn.cursor()
            cur.execute("SELECT url, title FROM channels WHERE status='ok' LIMIT 10000")
            rows = cur.fetchall()
            for url, title in rows:
                if title:
                    _ = fetch_metadata_for_title(conn, title)
            if LOCAL_PLAYLIST.exists():
                git_push_local()
            log.info("📊 Total in playlist: %d", len(WRITTEN_CHANNELS))
            time.sleep(UPDATE_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt received – exiting main loop")
            break
        except Exception as e:
            log.exception("Main loop error")
            time.sleep(60)

if __name__ == '__main__':
    log.info("🚀 VENGATESH IPTV GOLIATH - AI Continuous Mode")
    ensure_playlist_header()
    load_existing_playlist_channels()
    main_loop()
