import os
import time
import requests
import urllib.parse
import base64
import re
from flask import Flask, request, jsonify, render_template_string, redirect, session, make_response

app = Flask(__name__)
app.secret_key = "super_secret_car_lyrics_key"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Spotify</title>
    <!-- Geometric All-Caps Premium Font -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;800;900&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.0/color-thief.umd.js"></script>
    <style>
        body { 
            background-color: #121212; 
            color: white; 
            font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            height: 100vh; 
            width: 100vw;
            margin: 0; 
            overflow: hidden;
            transition: background-color 2.5s cubic-bezier(0.16, 1, 0.3, 1); 
        }
        
        /* Ambient breathing background effect */
        body::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.05) 0%, rgba(0,0,0,0) 70%);
            animation: breathe 8s infinite alternate cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            z-index: 0;
        }

        @keyframes breathe {
            0% { transform: scale(1); opacity: 0.3; }
            100% { transform: scale(1.4); opacity: 1; }
        }

        .login-container { 
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 90%; 
            max-width: 360px; 
            gap: 16px;
            z-index: 10;
            animation: fadeIn 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        
        .pill-input { 
            display: flex; 
            align-items: center;
            justify-content: center;
            padding: 14px 18px; 
            width: 100%; 
            box-sizing: border-box;
            border-radius: 14px; 
            border: 1px solid rgba(255,255,255,0.1); 
            font-size: 13px; 
            font-weight: 700;
            font-family: inherit;
            text-transform: inherit;
            letter-spacing: inherit;
            background: rgba(20, 20, 20, 0.75); 
            backdrop-filter: blur(15px);
            color: white;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        }
        input.pill-input { outline: none; }
        input.pill-input::placeholder { color: #777; text-align: center; }
        .pill-input:hover {
            border-color: #1DB954;
            box-shadow: 0 0 22px rgba(29, 185, 84, 0.4);
            transform: translateY(-2px);
        }
        
        .pill-button { 
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            background: #1DB954; 
            color: white; 
            border: none; 
            padding: 14px 20px; 
            border-radius: 14px; 
            cursor: pointer; 
            width: 100%; 
            box-sizing: border-box;
            height: 50px;
            font-size: 14px;
            font-weight: 800;
            font-family: inherit;
            text-transform: inherit;
            letter-spacing: inherit;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 8px 25px rgba(29, 185, 84, 0.4);
        }
        .pill-button:hover { 
            transform: translateY(-2px) scale(1.02); 
            background: #1ed760;
            box-shadow: 0 12px 30px rgba(29, 185, 84, 0.6);
        }

        #lyrics-container { 
            display: flex; 
            width: 90vw; 
            height: 100vh; 
            position: relative; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            text-align: center;
            gap: 4vh;
            z-index: 10;
            animation: fadeIn 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        
        .lyric-line { 
            width: 100%;
            display: flex;
            justify-content: center;
            transform-origin: center center;
            transition: transform 0.4s ease; 
        }
        
        .lyric-inner {
            white-space: nowrap;
            padding: 0 20px;
            will-change: transform, opacity, filter;
        }
        
        .adjacent-line .lyric-inner { 
            opacity: 0.3; 
            font-size: clamp(16px, 3.5vw, 26px);
            font-weight: 600;
            filter: blur(1.5px);
        }
        
        .active-line .lyric-inner { 
            opacity: 1; 
            font-size: clamp(24px, 5.5vw, 46px); 
            font-weight: 900;
            filter: blur(0px);
            text-shadow: 0 4px 35px rgba(0,0,0,0.65); 
        }

        /* Seamless liquid glide animations triggered on text change */
        @keyframes lyricPop {
            0% { transform: translateY(15px) scale(0.95); opacity: 0; filter: blur(5px); }
            100% { transform: translateY(0) scale(1); opacity: 1; filter: blur(0px); }
        }
        @keyframes lyricFade {
            0% { transform: translateY(10px); opacity: 0; filter: blur(3px); }
            100% { transform: translateY(0); opacity: 0.3; filter: blur(1.5px); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        #album-art-hidden { display: none; }
    </style>
</head>
<body>

    {% if error %}
    <div class="login-container">
        <h2 style="color: #ff4d4d; letter-spacing: 3px; font-weight: 900; margin-bottom: 5px;">ERROR</h2>
        <p style="color: #aaa; font-size: 11px; text-align: center; margin-bottom: 25px; font-weight: 600; letter-spacing: 1px;">{{ error }}</p>
        <a href="/" class="pill-button" style="background: rgba(30, 30, 30, 0.9); border: 1px solid rgba(255,255,255,0.1);">TRY AGAIN</a>
    </div>
    {% elif not is_authed %}
    <div class="login-container">
        <form action="/auth" method="POST" style="width: 100%; display: flex; flex-direction: column; gap: 16px; align-items: center;">
            <div class="pill-input" style="background: rgba(15, 15, 15, 0.6); color: #777; cursor: default; font-size: 11px;">{{ redirect_uri }}</div>
            <input type="text" name="client_id" class="pill-input" placeholder="client id" autocomplete="off" required />
            <input type="text" name="client_secret" class="pill-input" placeholder="client secret" autocomplete="off" required />
            <button type="submit" class="pill-button">connect</button>
        </form>
    </div>
    {% else %}
    <img id="album-art-hidden" crossorigin="anonymous" />
    
    <div id="lyrics-container">
        <div class="lyric-line adjacent-line" id="prev-line"><div class="lyric-inner"></div></div>
        <div class="lyric-line active-line" id="active-line"><div class="lyric-inner"></div></div>
        <div class="lyric-line adjacent-line" id="next-line"><div class="lyric-inner"></div></div>
    </div>

    <script>
        const colorThief = new ColorThief();
        let cachedTrackId = "";
        let parsedLines = [];
        let wakeLock = null;

        let serverProgress = 0;
        let serverTimestamp = 0;
        let isPlaying = false;
        let lastActiveIndex = -1;

        async function requestWakeLock() {
            try {
                if ('wakeLock' in navigator) {
                    wakeLock = await navigator.wakeLock.request('screen');
                    wakeLock.addEventListener('release', () => { wakeLock = null; });
                }
            } catch (err) {}
        }

        document.addEventListener('visibilitychange', async () => {
            if (wakeLock === null && document.visibilityState === 'visible') {
                await requestWakeLock();
            }
        });

        requestWakeLock();

        window.addEventListener('beforeunload', () => {
            navigator.sendBeacon('/logout');
        });

        function updateLine(elId, text, isActive) {
            const el = document.getElementById(elId);
            const inner = el.querySelector('.lyric-inner');
            
            if (inner.innerText !== text) {
                // Remove animation, trigger reflow, and swap text
                inner.style.animation = 'none';
                void inner.offsetWidth; 
                inner.innerText = text;

                // Dynamically auto-scale outer container to prevent text wrapping
                el.style.transform = 'none';
                const containerWidth = el.clientWidth - 40;
                const textWidth = inner.scrollWidth;
                if (textWidth > containerWidth && containerWidth > 0) {
                    const scaleFactor = containerWidth / textWidth;
                    el.style.transform = `scale(${scaleFactor})`;
                } else {
                    el.style.transform = 'scale(1)';
                }

                // Immediately trigger liquid pop/fade animation
                if (text.trim() !== "") {
                    if (isActive) {
                        inner.style.animation = 'lyricPop 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards';
                    } else {
                        inner.style.animation = 'lyricFade 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards';
                    }
                }
            }
        }

        async function pollServer() {
            try {
                const fetchStart = performance.now();
                const res = await fetch('/api/now-playing');
                const data = await res.json();
                const fetchEnd = performance.now();
                
                // Calculate exact network latency to align the visual clock perfectly
                const networkLatency = (fetchEnd - fetchStart) / 2;
                
                if (data.isPlaying) {
                    isPlaying = true;
                    serverProgress = data.progressMs;
                    serverTimestamp = performance.now() - networkLatency;

                    if (cachedTrackId !== data.trackId) {
                        cachedTrackId = data.trackId;
                        parsedLines = data.lines || [];
                        lastActiveIndex = -1;

                        updateLine('prev-line', '', false);
                        updateLine('active-line', '', true);
                        updateLine('next-line', '', false);

                        if (data.albumArt) {
                            const img = document.getElementById('album-art-hidden');
                            img.onload = () => {
                                try {
                                    const color = colorThief.getColor(img);
                                    const maxC = Math.max(color[0], color[1], color[2], 1);
                                    const scale = Math.min(1, 65 / maxC);
                                    const r = Math.floor(color[0] * scale);
                                    const g = Math.floor(color[1] * scale);
                                    const b = Math.floor(color[2] * scale);
                                    document.body.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
                                } catch(e) {}
                            };
                            img.src = data.albumArt;
                        }
                    }
                } else {
                    isPlaying = false;
                    updateLine('prev-line', '', false);
                    updateLine('active-line', '', true);
                    updateLine('next-line', '', false);
                }
            } catch(e) {}
        }

        // Tighter polling interval limits drift and keeps everything ruthlessly synced
        setInterval(pollServer, 750);
        pollServer();

        function animationLoop() {
            if (isPlaying && parsedLines.length > 0) {
                const currentProgress = serverProgress + (performance.now() - serverTimestamp);

                let activeIndex = -1;
                for (let i = 0; i < parsedLines.length; i++) {
                    // Triggers exactly on the millisecond timestamp—zero artificial delay
                    if (parsedLines[i].startTimeMs <= currentProgress) {
                        activeIndex = i;
                    }
                }

                if (activeIndex !== lastActiveIndex) {
                    lastActiveIndex = activeIndex;

                    const prevText = activeIndex > 0 ? parsedLines[activeIndex - 1].words : "";
                    const activeText = activeIndex >= 0 ? parsedLines[activeIndex].words : "";
                    const nextText = activeIndex + 1 < parsedLines.length ? parsedLines[activeIndex + 1].words : "";

                    updateLine('prev-line', prevText, false);
                    updateLine('active-line', activeText, true);
                    updateLine('next-line', nextText, false);
                }
            } else if (!isPlaying) {
                updateLine('prev-line', '', false);
                updateLine('active-line', '', true);
                updateLine('next-line', '', false);
            }
            requestAnimationFrame(animationLoop);
        }
        requestAnimationFrame(animationLoop);
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    is_authed = 'access_token' in session
    error_msg = request.args.get('error')
    redirect_uri = request.url_root.replace('http://', 'https://').rstrip('/') + '/callback'
    return render_template_string(HTML_TEMPLATE, is_authed=is_authed, redirect_uri=redirect_uri, error=error_msg)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    resp = make_response('', 204)
    resp.set_cookie('session', '', expires=0)
    return resp

@app.route('/auth', methods=['POST'])
def auth():
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    
    if not client_id or not client_secret:
        return redirect(f'/?error={urllib.parse.quote("Missing Credentials")}')
        
    client_id = client_id.strip()
    client_secret = client_secret.strip()
    session['client_id'] = client_id
    session['client_secret'] = client_secret
    
    redirect_uri = request.url_root.replace('http://', 'https://').rstrip('/') + '/callback'
    session['redirect_uri'] = redirect_uri

    scope = "user-read-currently-playing"
    
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri
    })
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(f'/?error={urllib.parse.quote("Authorization Cancelled")}')

    client_id = session.get('client_id')
    client_secret = session.get('client_secret')
    redirect_uri = session.get('redirect_uri')
    
    if not client_id or not client_secret:
        return redirect(f'/?error={urllib.parse.quote("Session Expired")}')

    auth_base64 = str(base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")), "utf-8")

    res = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
    )

    if not res.ok:
        return redirect(f'/?error={urllib.parse.quote("Invalid Client ID or Secret")}')

    data = res.json()
    session['access_token'] = data.get('access_token')
    session['refresh_token'] = data.get('refresh_token')
    session['expires_at'] = time.time() + data.get('expires_in', 3600) - 60

    return redirect('/')

def get_valid_token():
    if time.time() < session.get('expires_at', 0):
        return session.get('access_token')
        
    auth_base64 = str(base64.b64encode(f"{session['client_id']}:{session['client_secret']}".encode("utf-8")), "utf-8")
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_base64}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "refresh_token", "refresh_token": session['refresh_token']}
    )
    
    if res.ok:
        data = res.json()
        session['access_token'] = data.get('access_token')
        session['expires_at'] = time.time() + data.get('expires_in', 3600) - 60
        return session['access_token']
    return None

def parse_lrc(lrc_text):
    lines = []
    for line in lrc_text.split('\n'):
        match = re.match(r'\[(\d+):(\d+\.\d+)\](.*)', line)
        if match:
            mins, secs, words = int(match.group(1)), float(match.group(2)), match.group(3).strip()
            if words:
                lines.append({"startTimeMs": int((mins * 60 + secs) * 1000), "words": words})
    return lines

@app.route('/api/now-playing')
def now_playing():
    if not session.get('access_token'):
        return jsonify({"isPlaying": False, "error": "Not logged in"})
        
    token = get_valid_token()
    if not token:
         return jsonify({"isPlaying": False, "error": "Token refresh failed"})
         
    player_res = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if player_res.status_code == 204 or not player_res.ok:
        return jsonify({"isPlaying": False})
        
    player = player_res.json()
    if not player.get('item'):
        return jsonify({"isPlaying": False})
        
    track_id = player['item']['id']
    track_name = player['item']['name']
    artist_name = player['item']['artists'][0]['name']
    album_name = player['item'].get('album', {}).get('name', '')
    duration_secs = player['item'].get('duration_ms', 0) // 1000
    
    album_art = ""
    if player['item'].get('album') and player['item']['album'].get('images'):
        album_art = player['item']['album']['images'][0]['url']
    
    lines = []
    
    # 1. Clean track name properly to massively improve LRCLIB fallback search accuracy without crashing
    cleaned_name = re.sub(r'\s*[\(\[].*?(feat\.\vert{}ft\.\vert{}remaster\vert{}version\vert{}mix).*?[\)\]]', '', track_name, flags=re.IGNORECASE)
    cleaned_name = re.sub(r'\s*-.*?(Remaster|Live|Mono|Stereo).*', '', cleaned_name, flags=re.IGNORECASE).strip()
    
    # 2. Search LRCLIB with full exact track name
    try:
        search_res = requests.get("https://lrclib.net/api/search", params={
            "q": f"{track_name} {artist_name}"
        }, headers={"User-Agent": "InCarLyricsApp/1.0"}, timeout=3)
        
        if search_res.ok:
            search_data = search_res.json()
            for track in search_data:
                if track.get('syncedLyrics'):
                    lines = parse_lrc(track['syncedLyrics'])
                    break
    except Exception as e:
        pass

    # 3. Fallback: Search LRCLIB with cleaned track name (removes feats and tags)
    if not lines and cleaned_name != track_name:
        try:
            search_res = requests.get("https://lrclib.net/api/search", params={
                "q": f"{cleaned_name} {artist_name}"
            }, headers={"User-Agent": "InCarLyricsApp/1.0"}, timeout=3)
            
            if search_res.ok:
                search_data = search_res.json()
                for track in search_data:
                    if track.get('syncedLyrics'):
                        lines = parse_lrc(track['syncedLyrics'])
                        break
        except Exception as e:
            pass

    # 4. Final Fallback: Exact match via /api/get
    if not lines:
        try:
            get_res = requests.get("https://lrclib.net/api/get", params={
                "track_name": track_name, 
                "artist_name": artist_name,
                "album_name": album_name,
                "duration": duration_secs
            }, headers={"User-Agent": "InCarLyricsApp/1.0"}, timeout=3)
            
            if get_res.ok:
                get_data = get_res.json()
                if get_data.get('syncedLyrics'):
                    lines = parse_lrc(get_data['syncedLyrics'])
        except Exception as e:
            pass

    return jsonify({
        "isPlaying": player.get('is_playing', False),
        "progressMs": player.get('progress_ms', 0),
        "title": track_name,
        "artist": artist_name,
        "albumArt": album_art,
        "trackId": track_id,
        "lines": lines
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)