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
            height: 100dvh;
            width: 100vw;
            margin: 0; 
            overflow: hidden;
            transition: background-color 2.5s cubic-bezier(0.16, 1, 0.3, 1); 
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
            transition: all 0.4s ease;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        }
        input.pill-input { outline: none; }
        input.pill-input::placeholder { color: #777; text-align: center; }
        .pill-input:hover { border-color: #1DB954; }
        
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
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(29, 185, 84, 0.4);
        }
        .pill-button:active { transform: scale(0.97); }

        .error-text {
            color: white;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        #lyrics-container { 
            display: flex; 
            width: 90vw; 
            height: calc(100dvh - 100px); 
            position: relative; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            text-align: center;
            gap: 20px;
            z-index: 10;
        }
        
        .lyric-line { 
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.5s ease; 
        }
        
        .lyric-inner {
            white-space: pre-wrap;
            word-wrap: break-word;
            padding: 0 10px;
            max-width: 95vw;
            line-height: 1.2;
            transition: opacity 0.5s ease, font-size 0.5s ease, filter 0.5s ease;
        }
        
        .adjacent-line .lyric-inner { 
            opacity: 0.35; 
            font-size: clamp(16px, 3.5vw, 24px);
            font-weight: 600;
            filter: blur(1px);
        }
        
        .active-line .lyric-inner { 
            opacity: 1; 
            font-size: clamp(24px, 5.5vw, 42px); 
            font-weight: 900;
            filter: blur(0px);
            text-shadow: 0 4px 20px rgba(0,0,0,0.5); 
        }

        #controls-bar {
            position: absolute;
            bottom: 30px;
            display: flex;
            gap: 30px;
            align-items: center;
            justify-content: center;
            z-index: 20;
            background: rgba(0, 0, 0, 0.3);
            padding: 12px 30px;
            border-radius: 40px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .control-btn {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s ease, opacity 0.2s ease;
            opacity: 0.7;
        }
        
        .control-btn:hover, .control-btn:active {
            opacity: 1;
            transform: scale(1.1);
        }
        
        .control-btn svg {
            fill: white;
            width: 24px;
            height: 24px;
        }

        #album-art-hidden { display: none; }
    </style>
</head>
<body>

    {% if error %}
    <div class="login-container">
        <div class="error-text">CONNECTION ERROR</div>
        <div class="pill-input" style="background: rgba(15, 15, 15, 0.6); color: #999; cursor: default; font-size: 11px; margin-bottom: 10px;">{{ error }}</div>
        <a href="/" class="pill-button" style="background: rgba(40, 40, 40, 0.9); border: 1px solid rgba(255,255,255,0.1);">TRY AGAIN</a>
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

    <!-- Playback Controls -->
    <div id="controls-bar">
        <button class="control-btn" onclick="sendControl('previous')">
            <svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
        </button>
        <button class="control-btn" onclick="sendControl('playpause')">
            <svg viewBox="0 0 24 24" id="play-pause-icon"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <button class="control-btn" onclick="sendControl('next')">
            <svg viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
        </button>
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
                if ('wakeLock' in navigator && wakeLock === null) {
                    wakeLock = await navigator.wakeLock.request('screen');
                    wakeLock.addEventListener('release', () => { wakeLock = null; });
                }
            } catch (err) {}
        }
        document.body.addEventListener('click', requestWakeLock);
        document.body.addEventListener('touchstart', requestWakeLock);

        window.addEventListener('beforeunload', () => {
            navigator.sendBeacon('/logout');
        });

        async function sendControl(action) {
            requestWakeLock();
            try {
                await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                setTimeout(pollServer, 300);
            } catch (e) {}
        }

        function updatePlayPauseIcon() {
            const icon = document.getElementById('play-pause-icon');
            if (isPlaying) {
                icon.innerHTML = '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>';
            } else {
                icon.innerHTML = '<path d="M8 5v14l11-7z"/>';
            }
        }

        function updateLine(elId, text) {
            const inner = document.getElementById(elId).querySelector('.lyric-inner');
            if (inner.innerText !== text) {
                inner.innerText = text;
            }
        }

        async function pollServer() {
            try {
                const fetchStart = performance.now();
                const res = await fetch(`/api/now-playing?t=${Date.now()}`);
                const data = await res.json();
                const fetchEnd = performance.now();
                const networkLatency = (fetchEnd - fetchStart) / 2;
                
                if (data.isPlaying && data.trackId) {
                    isPlaying = true;
                    serverProgress = data.progressMs;
                    serverTimestamp = performance.now() - networkLatency;
                    updatePlayPauseIcon();

                    if (cachedTrackId !== data.trackId) {
                        cachedTrackId = data.trackId;
                        parsedLines = data.lines || [];
                        lastActiveIndex = -1;

                        updateLine('prev-line', '');
                        updateLine('active-line', '');
                        updateLine('next-line', '');

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
                    updatePlayPauseIcon();
                    updateLine('prev-line', '');
                    updateLine('active-line', '');
                    updateLine('next-line', '');
                    
                    if (!data.trackId) {
                        cachedTrackId = "";
                    }
                }
            } catch(e) {}
        }

        setInterval(pollServer, 800);
        pollServer();

        function animationLoop() {
            if (isPlaying && parsedLines.length > 0) {
                const currentProgress = serverProgress + (performance.now() - serverTimestamp);

                let activeIndex = -1;
                for (let i = 0; i < parsedLines.length; i++) {
                    if (parsedLines[i].startTimeMs <= currentProgress) {
                        activeIndex = i;
                    }
                }

                if (activeIndex !== lastActiveIndex) {
                    lastActiveIndex = activeIndex;

                    const prevText = activeIndex > 0 ? parsedLines[activeIndex - 1].words : "";
                    const activeText = activeIndex >= 0 ? parsedLines[activeIndex].words : "";
                    const nextText = activeIndex + 1 < parsedLines.length ? parsedLines[activeIndex + 1].words : "";

                    updateLine('prev-line', prevText);
                    updateLine('active-line', activeText);
                    updateLine('next-line', nextText);
                }
            } else if (!isPlaying) {
                updateLine('prev-line', '');
                updateLine('active-line', '');
                updateLine('next-line', '');
            }
            requestAnimationFrame(animationLoop);
        }
        requestAnimationFrame(animationLoop);
    </script>
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

    scope = "user-read-currently-playing user-modify-playback-state"
    
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

    try:
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
    except Exception:
        return redirect(f'/?error={urllib.parse.quote("Spotify Connection Error")}')

    return redirect('/')

def get_valid_token():
    if time.time() < session.get('expires_at', 0):
        return session.get('access_token')
        
    client_id = session.get('client_id', '')
    client_secret = session.get('client_secret', '')
    if not client_id or not client_secret:
        return None

    auth_base64 = str(base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")), "utf-8")
    try:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth_base64}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "refresh_token", "refresh_token": session.get('refresh_token', '')}
        )
        
        if res.ok:
            data = res.json()
            session['access_token'] = data.get('access_token')
            session['expires_at'] = time.time() + data.get('expires_in', 3600) - 60
            return session['access_token']
    except Exception:
        pass
        
    return None

def parse_lrc(lrc_text):
    if not lrc_text or not isinstance(lrc_text, str):
        return []
    lines = []
    for line in lrc_text.split('\n'):
        match = re.match(r'\[(\d+):(\d+\.\d+)\](.*)', line)
        if match:
            mins, secs, words = int(match.group(1)), float(match.group(2)), match.group(3).strip()
            if words:
                lines.append({"startTimeMs": int((mins * 60 + secs) * 1000), "words": words})
    return lines

@app.route('/api/control', methods=['POST'])
def control():
    token = get_valid_token()
    if not token:
        return jsonify({"success": False, "error": "Not logged in"})
        
    payload = request.get_json(silent=True) or {}
    action = payload.get('action')
    
    try:
        if action == 'playpause':
            state_res = requests.get(
                "https://api.spotify.com/v1/me/player",
                headers={"Authorization": f"Bearer {token}"}
            )
            if state_res.ok and state_res.status_code != 204:
                is_playing = state_res.json().get('is_playing', False)
                endpoint = "pause" if is_playing else "play"
                requests.put(f"https://api.spotify.com/v1/me/player/{endpoint}", headers={"Authorization": f"Bearer {token}"})
                return jsonify({"success": True})
        
        elif action in ['next', 'previous']:
            requests.post(f"https://api.spotify.com/v1/me/player/{action}", headers={"Authorization": f"Bearer {token}"})
            return jsonify({"success": True})
    except Exception:
        pass
        
    return jsonify({"success": False})

@app.route('/api/now-playing')
def now_playing():
    token = get_valid_token()
    if not token:
         return jsonify({"isPlaying": False, "error": "Token missing"})
         
    try:
        player_res = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {token}"},
            timeout=4
        )
    except Exception:
        return jsonify({"isPlaying": False, "trackId": None})
    
    if player_res.status_code == 204 or not player_res.ok:
        return jsonify({"isPlaying": False, "trackId": None})
        
    try:
        player = player_res.json()
    except Exception:
        return jsonify({"isPlaying": False, "trackId": None})

    item = player.get('item') or {}
    track_id = item.get('id') or ""
    track_name = item.get('name') or ""
    artists = item.get('artists') or []
    artist_name = artists[0].get('name', '') if artists and isinstance(artists[0], dict) else ""
    
    if not track_name or not artist_name:
        return jsonify({"isPlaying": False, "trackId": None})
    
    album = item.get('album') or {}
    images = album.get('images') or []
    album_art = images[0].get('url', '') if images and isinstance(images[0], dict) else ""
    
    lines = []
    
    # Safe regex string stripping
    cleaned_name = re.sub(r'\s*[\(\[].*?(feat\.\vert{}ft\.\vert{}remaster\vert{}version\vert{}mix).*?[\)\]]', '', track_name, flags=re.IGNORECASE)
    cleaned_name = re.sub(r'\s*-.*?(Remaster|Live|Mono|Stereo).*', '', cleaned_name, flags=re.IGNORECASE).strip()
    
    try:
        search_res = requests.get("https://lrclib.net/api/search", params={
            "q": f"{cleaned_name} {artist_name}"
        }, headers={"User-Agent": "InCarLyricsApp/1.0"}, timeout=3)
        
        if search_res.ok:
            search_data = search_res.json()
            if isinstance(search_data, list):
                for track in search_data:
                    if isinstance(track, dict) and track.get('syncedLyrics'):
                        lines = parse_lrc(track['syncedLyrics'])
                        break
    except Exception:
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