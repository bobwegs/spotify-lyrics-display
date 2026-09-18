import os
import time
import requests
import urllib.parse
import base64
import re
from flask import Flask, request, jsonify, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "super_secret_car_lyrics_key"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>In-Car Lyrics</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.0/color-thief.umd.js"></script>
    <style>
        body { 
            background: #121212; 
            color: white; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            height: 100vh; 
            width: 100vw;
            margin: 0; 
            overflow: hidden;
            transition: background 1.5s cubic-bezier(0.4, 0, 0.2, 1); 
        }
        .login-box { 
            background: rgba(40, 40, 40, 0.9); 
            padding: 2rem; 
            border-radius: 12px; 
            text-align: center; 
            width: 85%; 
            max-width: 400px; 
            box-shadow: 0 8px 24px rgba(0,0,0,0.5); 
        }
        input { display: block; margin: 15px auto; padding: 12px; width: 85%; border-radius: 6px; border: none; font-size: 16px; background: #333; color: white;}
        button { background: #1DB954; color: white; border: none; padding: 14px 20px; border-radius: 30px; font-weight: bold; cursor: pointer; width: 93%; font-size: 16px; transition: transform 0.2s;}
        button:hover { transform: scale(1.04); }
        
        /* True center-locked 3-line fixed layout with smooth animations */
        #lyrics-container { 
            display: flex; 
            width: 90vw; 
            height: 100vh; 
            position: relative; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            text-align: center;
            gap: 3.5vh;
        }
        
        .lyric-line { 
            width: 100%;
            word-break: break-word;
            padding: 0 20px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Adjacent (Previous/Next) lines: smooth fade and subtle scale */
        .adjacent-line { 
            opacity: 0.35; 
            font-size: clamp(18px, 3.5vw, 30px);
            font-weight: 600;
            filter: blur(0.3px);
            transform: scale(0.97);
        }
        
        /* Active line: permanently dead-center, large, bright, and vibrant */
        .active-line { 
            opacity: 1; 
            font-size: clamp(26px, 5.5vw, 52px); 
            font-weight: 800;
            filter: blur(0px);
            transform: scale(1);
            text-shadow: 0 4px 25px rgba(0,0,0,0.5); 
        }
        
        #album-art-hidden { display: none; }
    </style>
</head>
<body>

    {% if not is_authed %}
    <div class="login-box">
        <h2 style="color: #1DB954; margin-top: 0;">Spotify Engine</h2>
        <p style="color: #b3b3b3; font-size: 14px; margin-bottom: 10px;">Set this exact Redirect URI in your Spotify Dashboard:</p>
        <code style="display: block; background: #111; padding: 12px; border-radius: 6px; margin-bottom: 25px; color: #1DB954; font-size: 13px; user-select: all;">https://spotify-lyrics-display.onrender.com/callback</code>
        <form action="/auth" method="POST">
            <input type="text" name="client_id" placeholder="Client ID" required />
            <input type="password" name="client_secret" placeholder="Client Secret" required />
            <button type="submit">Connect to Spotify</button>
        </form>
    </div>
    {% else %}
    <img id="album-art-hidden" crossorigin="anonymous" />
    
    <div id="lyrics-container">
        <div id="prev-line" class="lyric-line adjacent-line"></div>
        <div id="active-line" class="lyric-line active-line"></div>
        <div id="next-line" class="lyric-line adjacent-line"></div>
    </div>

    <script>
        const colorThief = new ColorThief();
        let cachedTrackId = "";
        let parsedLines = [];
        let wakeLock = null;

        // Robust Wake Lock implementation to keep screen alive
        async function requestWakeLock() {
            try {
                if ('wakeLock' in navigator) {
                    wakeLock = await navigator.wakeLock.request('screen');
                    wakeLock.addEventListener('release', () => {
                        wakeLock = null;
                    });
                }
            } catch (err) {
                console.error("Wake Lock error:", err);
            }
        }

        // Re-acquire wake lock if page becomes visible again
        document.addEventListener('visibilitychange', async () => {
            if (wakeLock === null && document.visibilityState === 'visible') {
                await requestWakeLock();
            }
        });

        requestWakeLock();

        // Guaranteed auto-logout on refresh, navigation, or tab close
        window.addEventListener('beforeunload', () => {
            navigator.sendBeacon('/logout');
        });

        async function pollLyrics() {
            try {
                const res = await fetch('/api/now-playing');
                const data = await res.json();
                
                if(data.isPlaying) {
                    if (cachedTrackId !== data.trackId) {
                        cachedTrackId = data.trackId;
                        parsedLines = data.lines || [];
                        
                        if (data.albumArt) {
                            const img = document.getElementById('album-art-hidden');
                            img.onload = () => {
                                try {
                                    const color = colorThief.getColor(img);
                                    document.body.style.background = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
                                } catch(e) {}
                            };
                            img.src = data.albumArt;
                        }
                    }

                    let activeIndex = -1;
                    for (let i = 0; i < parsedLines.length; i++) {
                        if (parsedLines[i].startTimeMs <= data.progressMs) {
                            activeIndex = i;
                        }
                    }

                    const prevEl = document.getElementById('prev-line');
                    const activeEl = document.getElementById('active-line');
                    const nextEl = document.getElementById('next-line');

                    if (parsedLines.length > 0) {
                        prevEl.innerText = activeIndex > 0 ? parsedLines[activeIndex - 1].words : "";
                        activeEl.innerText = activeIndex >= 0 ? parsedLines[activeIndex].words : "♪";
                        nextEl.innerText = activeIndex + 1 < parsedLines.length ? parsedLines[activeIndex + 1].words : "";
                    } else {
                        prevEl.innerText = "";
                        activeEl.innerText = "♪ " + data.title + " ♪";
                        nextEl.innerText = "";
                    }
                } else {
                    document.getElementById('prev-line').innerText = "";
                    document.getElementById('active-line').innerText = "";
                    document.getElementById('next-line').innerText = "";
                }
            } catch(e) {
                console.error(e);
            }
        }
        setInterval(pollLyrics, 1000);
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    is_authed = 'access_token' in session
    return render_template_string(HTML_TEMPLATE, is_authed=is_authed)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return '', 204

@app.route('/auth', methods=['POST'])
def auth():
    client_id = request.form.get('client_id').strip()
    client_secret = request.form.get('client_secret').strip()
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
        return "Error: Authorization failed. Try again."

    client_id = session.get('client_id')
    client_secret = session.get('client_secret')
    redirect_uri = session.get('redirect_uri')

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
        return f"Failed to authenticate with Spotify: {res.text}"

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
    
    album_art = ""
    if player['item'].get('album') and player['item']['album'].get('images'):
        album_art = player['item']['album']['images'][0]['url']
    
    lines = []
    lrc_res = requests.get("https://lrclib.net/api/get", params={"track_name": track_name, "artist_name": artist_name})
    
    if lrc_res.ok:
        lrc_data = lrc_res.json()
        if lrc_data.get('syncedLyrics'):
            lines = parse_lrc(lrc_data['syncedLyrics'])

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