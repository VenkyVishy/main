#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VENGATESH IPTV - V22.1 GITHUB-AWARE ENGINE (FIXED)

FIXES:
- ✅ No 'coroutine not iterable' error
- ✅ Proper scoping of aiohttp session
- ✅ GitHub repos cloned synchronously
- ✅ Raw URLs fetched asynchronously
- ✅ All your links preserved — none omitted
- ✅ Real-time validation & addition
- ✅ Cloudflare URL shown immediately
"""

import os
import sys
import asyncio
import aiohttp
import time
import re
import shutil
import socket
import random
import json
import hashlib
import atexit
import threading
import subprocess
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# --- CONFIG ---
UPDATE_INTERVAL = 1800
FETCH_TIMEOUT = 8
VALIDATE_TIMEOUT = 6
MAX_CONCURRENT_FETCHES = 60
MAX_VALIDATION_THREADS = 12
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".vengatesh_iptv_v22")
PLAYLIST_FILE = os.path.join(CONFIG_DIR, "github_aware_playlist.m3u")
PERSISTENCE_FILE = os.path.join(CONFIG_DIR, "validated_github.json")
TEMP_DIR = os.path.join(CONFIG_DIR, "temp_repos")
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- GLOBAL STATE ---
accumulated_lock = threading.RLock()
global_accumulated = {}
global_total = 0
cloudflare_url = None
cloudflare_ready = asyncio.Event()
playlist_update_lock = asyncio.Lock()

# --- PROXIES ---
FREE_PROXIES = [
    ("103.152.232.210", 8080),
    ("45.79.253.142", 3128),
    ("185.162.230.114", 8080),
    ("103.48.68.35", 83),
    ("103.159.46.10", 8080),
    ("45.167.92.146", 9992),
    ("103.152.112.162", 80),
    ("103.117.192.14", 80),
    ("103.48.68.36", 84),
    ("103.159.46.14", 8080),
]

# --- EPG SOURCES ---
EPG_SOURCES = [
    "https://iptv-org.github.io/epg/guides/ALL.xml.gz",
    "https://raw.githubusercontent.com/mitthu786/tvepg/main/tataplay/epg.xml.gz",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/in.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/us.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/uk.xml",
    "https://epg.provider.iptvorg.org/epg.xml.gz",
    "https://raw.githubusercontent.com/koditv/epg/main/epg.xml"
]

# --- FULL SOURCE LIST (YOUR ORIGINAL LINKS) ---
ALL_SOURCES = [
    "https://github.com/iptv-org/iptv.git",
    "https://github.com/Free-TV/IPTV.git",
    "https://github.com/JioTV-Go/jiotv_go.git",
    "https://github.com/mitthu786/TS-JioTV.git",
    "https://iptv-org.github.io/iptv/index.language.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u",
    "https://raw.githubusercontent.com/EvilCaster/IPTV/master/iptv.txt",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/live.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/catchup.m3u",
    "https://raw.githubusercontent.com/mitthu786/TS-JioTV/main/allChannels.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/channels.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/backup.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/tv.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/live_tv.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/free.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/premium.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages.m3u",
    "https://raw.githubusercontent.com/ivandimov1/iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/git-up/IPTV/master/playlist.m3u",
    "https://raw.githubusercontent.com/ImJanindu/IPTV/main/IPTV.m3u",
    "https://raw.githubusercontent.com/azam00789/IPTV/main/playlist.m3u",
    "https://raw.githubusercontent.com/blackheart001/IPTV/main/playlist.m3u",
    "https://raw.githubusercontent.com/6eorge/iptv/master/playlist.m3u",
    "https://raw.githubusercontent.com/Aretera/IPTV/master/playlist.m3u",
    "https://raw.githubusercontent.com/ombori/iptv-playlist/master/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/regions.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/subdivisions.m3u",
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
    "https://bit.ly/2E2uz5S",
    "https://tinyurl.com/amaze-tamil-local-tv",
    "https://bit.ly/3h5yNZM",
    "https://bit.ly/3Jk4d7L",
    "https://bit.ly/3Lm2p9Q",
    "https://tinyurl.com/iptv-global-free",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u8",
    "https://sites.google.com/site/arvinthiptv/Home/arvinth.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u8",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/live.m3u8",
    "https://iptv-org.github.io/iptv/index.m3u8",
    "https://raw.githubusercontent.com/mitthu786/TS-JioTV/main/allChannels.m3u8",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/playlist.m3u8",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/ott.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/ott.m3u",
    "https://raw.githubusercontent.com/hrishi7/streamIt/main/playlist.m3u",
    "https://raw.githubusercontent.com/Free-IPTV/Countries/master/IN/movies.m3u",
    "https://raw.githubusercontent.com/Free-IPTV/Countries/master/US/movies.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/movies.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/series.m3u",
    "https://raw.githubusercontent.com/streamit-iptv/movies/main/playlist.m3u",
    "https://raw.githubusercontent.com/ott-stream/ultimate/main/movies.m3u",
    "https://raw.githubusercontent.com/ott-stream/ultimate/main/series.m3u",
    "https://raw.githubusercontent.com/movie-streams/m3u/main/movies.m3u",
    "https://raw.githubusercontent.com/series-streams/m3u/main/series.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/vod.m3u",
    "https://iptv-mirror.com/playlist.m3u",
    "https://backup-iptv.com/playlist.m3u",
    "https://iptv-reserve.net/playlist.m3u",
    "https://mirror.iptv-org.com/index.m3u",
    "https://raw.githubusercontent.com/sports-iptv/sports/main/playlist.m3u",
    "https://raw.githubusercontent.com/news-iptv/news/main/playlist.m3u",
    "https://raw.githubusercontent.com/music-iptv/music/main/playlist.m3u",
    "https://raw.githubusercontent.com/kids-iptv/kids/main/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/countries/au.m3u",
    "https://iptv-org.github.io/iptv/countries/au.m3u",
    "https://raw.githubusercontent.com/Free-IPTV/Countries/master/AU/tv.m3u",
    "https://raw.githubusercontent.com/aussie-iptv/streams/main/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/hin.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/languages/tam.m3u",
    "https://raw.githubusercontent.com/mitthu786/TS-JioTV/main/allChannels.m3u",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/playlist.m3u",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/playlist.m3u8",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/jio.m3u",
    "https://raw.githubusercontent.com/JioTV-Go/jiotv_go/main/jio.m3u8",
]

# --- PERSISTENCE ---
def load_persistence():
    global global_accumulated, global_total
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                global_accumulated = {item["url"]: item["info"] for item in data.get("validated", [])}
                global_total = len(global_accumulated)
                print(f"✅ Loaded {global_total:,} channels.")
        except Exception as e:
            print(f"⚠️  Load failed: {e}")

def save_persistence_at_exit():
    global global_accumulated
    try:
        data = {
            "total_validated": len(global_accumulated),
            "validated": [{"url": url, "info": info} for url, info in global_accumulated.items()]
        }
        with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Final persistence saved: {len(global_accumulated):,} channels.")
    except Exception as e:
        print(f"\n❌ Save failed: {e}")

atexit.register(save_persistence_at_exit)

# --- UTILS ---
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def extract_channel_name(info_line):
    match = re.search(r',([^,\n]*)$', info_line)
    if match:
        name = match.group(1).strip()
        if name and not name.startswith(('http', 'rtmp')):
            return name
    match = re.search(r'tvg-name=["\']?([^"\']*)', info_line)
    if match and match.group(1).strip():
        return match.group(1).strip()
    return hashlib.md5(info_line.encode()).hexdigest()[:12]

# --- GITHUB HANDLING (SYNC) ---
def is_github_repo(url):
    return url.strip().endswith('.git') and 'github.com' in url

def clone_github_repo(url):
    """Synchronous clone — NO async here."""
    try:
        repo_name = hashlib.md5(url.encode()).hexdigest()[:10]
        dest = os.path.join(TEMP_DIR, repo_name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        result = subprocess.run(
            ["git", "clone", "--depth=1", url, dest],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60
        )
        if result.returncode == 0:
            m3u_files = []
            for root, _, files in os.walk(dest):
                for f in files:
                    if f.endswith(('.m3u', '.m3u8', '.txt')):
                        m3u_files.append(os.path.join(root, f))
            return m3u_files
    except Exception:
        pass
    return []

def read_local_playlist(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

# --- FETCHING (ASYNC) ---
async def fetch_url(session, url):
    try:
        async with session.get(
            url.strip(),
            timeout=FETCH_TIMEOUT,
            headers={'User-Agent': 'VengateshIPTV/22.1'}
        ) as resp:
            if resp.status == 200:
                return await resp.text(encoding='utf-8', errors='ignore')
    except Exception:
        pass
    return ""

# --- VALIDATION (SYNC, for thread pool) ---
def validate_and_add(url, info, proxy_list, callback):
    if not url or not (url.startswith('http') or url.startswith('rtmp')):
        return
    def try_proxy(proxy):
        try:
            import urllib.request, socket
            timeout = VALIDATE_TIMEOUT
            if url.startswith('rtmp'):
                parsed = urlparse(url)
                host, port = parsed.hostname or 'localhost', parsed.port or 1935
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            else:
                req = urllib.request.Request(url)
                req.add_header('Range', 'bytes=0-512')
                req.add_header('User-Agent', 'VengateshIPTV/22.1')
                if proxy:
                    ph = urllib.request.ProxyHandler({'http': f'http://{proxy[0]}:{proxy[1]}', 'https': f'http://{proxy[0]}:{proxy[1]}'})
                    opener = urllib.request.build_opener(ph)
                    urllib.request.install_opener(opener)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.getcode() in (200, 206)
        except Exception:
            return False
    if try_proxy(None) or any(try_proxy(random.choice(proxy_list)) for _ in range(2)):
        callback(url, info)

async def write_playlist():
    async with playlist_update_lock:
        epg_str = ','.join(EPG_SOURCES)
        header = f'#EXTM3U x-tvg-url="{epg_str}"\n'
        body = "\n".join(f"{info}\n{url}" for url, info in global_accumulated.items())
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.write(header + body)

# --- DISCOVERY ---
async def discover_sources(session):
    discovered = set()
    countries = ["in", "us", "uk", "ca", "au", "de", "fr", "es", "it", "br", "mx", "ru", "jp", "kr", "sa", "ae", "za"]
    languages = ["tam", "hin", "eng", "spa", "fra", "deu", "por", "ara", "rus", "jpn", "kor"]
    for c in countries:
        discovered.add(f"https://raw.githubusercontent.com/iptv-org/iptv/master/countries/{c}.m3u")
    for l in languages:
        discovered.add(f"https://raw.githubusercontent.com/iptv-org/iptv/master/languages/{l}.m3u")
    for cat in ["news", "sports", "movies", "kids"]:
        discovered.add(f"https://raw.githubusercontent.com/iptv-org/iptv/master/categories/{cat}.m3u")
    try:
        async with session.get("https://iptv-org.github.io/iptv/index.m3u", timeout=10) as resp:
            if resp.status == 200:
                content = await resp.text()
                for line in content.split('\n'):
                    if line.startswith('http') and line.strip().endswith(('.m3u', '.m3u8')):
                        discovered.add(line.strip())
    except Exception:
        pass
    return list(discovered)

# --- MAIN FETCH PIPELINE ---
async def fetch_all_sources():
    github_repos = []
    direct_urls = []

    for url in ALL_SOURCES:
        clean = url.strip()
        if is_github_repo(clean):
            github_repos.append(clean)
        else:
            direct_urls.append(clean)

    # Clone GitHub repos (synchronous, in thread pool)
    contents = []
    loop = asyncio.get_event_loop()
    for repo_url in github_repos:
        print(f"📦 Cloning: {repo_url}")
        m3u_paths = await loop.run_in_executor(None, clone_github_repo, repo_url)
        for path in m3u_paths:
            content = await loop.run_in_executor(None, read_local_playlist, path)
            if content:
                contents.append(content)

    # Discover dynamic sources
    async with aiohttp.ClientSession() as session:
        dynamic_sources = await discover_sources(session)
        direct_urls.extend(dynamic_sources)

        # Fetch direct URLs
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
        async def limited_fetch(url):
            async with semaphore:
                return await fetch_url(session, url)
        direct_contents = await asyncio.gather(*[limited_fetch(url) for url in direct_urls])
        contents.extend([c for c in direct_contents if c])

    return contents

# --- CLOUDFLARE ---
async def start_cloudflared_early():
    global cloudflare_url
    if not shutil.which("cloudflared"):
        print("⚠️  cloudflared not found.")
        return
    print("🚀 Starting Cloudflare tunnel...")
    proc = await asyncio.create_subprocess_exec(
        "cloudflared", "tunnel", "--url", "http://localhost:8080", "--no-autoupdate",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8', errors='ignore')
        if "trycloudflare.com" in text:
            match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', text)
            if match:
                cloudflare_url = f"{match.group(0)}/playlist.m3u"
                print("\n" + "🌍" * 30)
                print(f"✅ CLOUDFLARE URL: {cloudflare_url}")
                print("🌍" * 30 + "\n")
                cloudflare_ready.set()
                break

# --- REAL-TIME CYCLE ---
async def run_github_cycle():
    global global_total
    print("📥 Fetching sources (cloning GitHub repos + downloading raw URLs)...")
    contents = await fetch_all_sources()

    candidate_streams = []
    for content in contents:
        lines = content.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                if i + 1 < len(lines):
                    url = lines[i+1].strip()
                    if url and (url.startswith('http') or url.startswith('rtmp')):
                        if url not in global_accumulated:
                            candidate_streams.append((url, line))
                i += 2
                continue
            i += 1

    print(f"🔍 Validating {len(candidate_streams)} streams (real-time)...")

    def on_valid(url, info):
        global global_total
        with accumulated_lock:
            if url not in global_accumulated:
                global_accumulated[url] = info
                global_total = len(global_accumulated)
                asyncio.run_coroutine_threadsafe(write_playlist(), asyncio.get_event_loop())
                print(f"✅ Added: {extract_channel_name(info)[:40]}... | Total: {global_total:,}")

    with ThreadPoolExecutor(max_workers=MAX_VALIDATION_THREADS) as executor:
        for url, info in candidate_streams:
            executor.submit(validate_and_add, url, info, FREE_PROXIES, on_valid)

    await write_playlist()
    return global_total

# --- SERVER ---
from aiohttp import web

async def serve_playlist(_):
    return web.FileResponse(PLAYLIST_FILE) if os.path.exists(PLAYLIST_FILE) else web.Response(status=404)

async def start_server():
    app = web.Application()
    app.router.add_get('/playlist.m3u', serve_playlist)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

# --- MAIN ---
async def main():
    print("\n" + "✅" * 30)
    print(" VENGATESH IPTV - V22.1 GITHUB-AWARE ENGINE ")
    print(" .git repos → cloned | raw URLs → downloaded ")
    print("✅" * 30)

    asyncio.create_task(start_cloudflared_early())
    await start_server()
    load_persistence()

    count = await run_github_cycle()

    try:
        await asyncio.wait_for(cloudflare_ready.wait(), timeout=15.0)
    except asyncio.TimeoutError:
        pass

    local_ip = get_local_ip()
    print("\n" + "="*60)
    print(f"🏠 LOCAL: http://{local_ip}:8080/playlist.m3u")
    if cloudflare_url:
        print(f"🌍 CLOUDFLARE: {cloudflare_url}")
    print(f"📊 TOTAL: {count:,}")
    print("="*60)

    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔄 CYCLE")
        await run_github_cycle()

if __name__ == "__main__":
    try:
        if "com.termux" in os.environ.get("PREFIX", ""):
            print("\n💡 Run 'termux-wake-lock' to prevent sleep.")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
    except Exception as e:
        print(f"\n❌ Fatal: {e}")
        sys.exit(1)
