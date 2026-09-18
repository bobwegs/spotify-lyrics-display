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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
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
            margin: 0; 
            transition: background 1.5s ease; /* Smooth transition for solid colors */
        }
        .login-box { background: rgba(40, 40, 40, 0.9); padding: 2rem; border-radius: 12px; text-align: center; width: 85%; max-width: 400px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        input { display: block; margin: 15px auto; padding: 12px; width: 85%; border-radius: 6px; border: none; font-size: 16px; background: #333; color: white;}
        button { background: #1DB954; color: white; border: none; padding: 14px 20px; border-radius: 30px; font-weight: bold; cursor: pointer; width: 93%; font-size: 16px; transition: transform 0.2s;}
        button:hover { transform: scale(1.04); }
        
        #lyrics-container { display: flex; width: 100%; height: 100vh; overflow: hidden; position: relative; flex-direction: column;}
        
        #track-header { 
            padding: 30px 20px 10px 30px; 
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 10;
        }
        #album-cover-img { width: 64px; height: 64px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: none; }
        .header-text { display: flex; flex-direction: column; }
        #track-title { color: #fff; margin: 0; font-size: 22px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        #track-artist { color: rgba(255,255,255,0.7); margin: 4px 0 0 0; font-size: 16px; font-weight: 500;}
        
        #lyrics-scroll { 
            flex-grow: 1; 
            overflow-y: auto; 
            padding: 30px; 
            padding-bottom: 60vh; 
            text-align: left;
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
        #lyrics-scroll::-webkit-scrollbar { display: none; }
        
        /* Spotify strict 3-line scrollable styling */
        .lyric-line { 
            font-size: 24px; 
            font-weight: 700; 
            margin: 20px 0; 
            transition: all 0.3s ease; 
            opacity: 0; /* Hides lines outside the 3-line window while keeping scroll height */
            color: #fff;
        }
        .adjacent-line { 
            opacity: 0.4; 
        }
        .active-line { 
            opacity: 1; 
            font-size: 38px; 
            text-shadow: 0 2px 10px rgba(0,0,0,0.2); 
        }
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
    <div id="lyrics-container">
        <div id="track-header">
            <img id="album-cover-img" crossorigin="anonymous" />
            <div class="header-text">
                <h3 id="track-title">Waiting for music...</h3>
                <p id="track-artist"></p>
            </div>
        </div>
        <div id="lyrics-scroll"></div>
    </div>

    <script>
        const colorThief = new ColorThief();

        async function pollLyrics() {
            try {
                const res = await fetch('/api/now-playing');
                const data = await res.json();
                
                if(data.isPlaying) {
                    document.getElementById('track-title').innerText = data.title;
                    document.getElementById('track-artist').innerText = data.artist;
                    
                    const scrollBox = document.getElementById('lyrics-scroll');
                    
                    if (scrollBox.dataset.trackId !== data.trackId) {
                        scrollBox.dataset.trackId = data.trackId;
                        scrollBox.innerHTML = ''; 
                        
                        if (data.albumArt) {
                            const img = document.getElementById('album-cover-img');
                            img.style.display = 'block';
                            img.onload = () => {
                                const color = colorThief.getColor(img);
                                // Sets a solid dominant color background
                                document.body.style.background = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
                            };
                            img.src = data.albumArt;
                        }
                        
                        if (data.lines && data.lines.length > 0) {
                            data.lines.forEach((line) => {
                                const div = document.createElement('div');
                                div.className = 'lyric-line';
                                div.innerText = line.words;
                                div.dataset.time = line.startTimeMs;
                                scrollBox.appendChild(div);
                            });
                        } else {
                            const div = document.createElement('div');
                            div.className = 'lyric-line active-line';
                            div.innerText = "♪";
                            scrollBox.appendChild(div);
                        }
                    }

                    let activeIndex = -1;
                    const lines = document.getElementsByClassName('lyric-line');
                    for (let i = 0; i < lines.length; i++) {
                        if (lines[i].dataset.time && data.progressMs >= parseInt(lines[i].dataset.time)) {
                            activeIndex = i;
                        }
                    }
                    
                    // Display only Previous, Current, and Next lines
                    for (let i = 0; i < lines.length; i++) {
                        if (i === activeIndex) {
                            if (!lines[i].classList.contains('active-line')) {
                                lines[i].className = 'lyric-line active-line';
                                lines[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                        } else if (i === activeIndex - 1 || i === activeIndex + 1) {
                            lines[i].className = 'lyric-line adjacent-line';
                        } else {
                            lines[i].className = 'lyric-line'; // Reverts to opacity: 0
                        }
                    }
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

@app.route('/auth', methods=['POST'])
def auth():
    client_id = request.form.get('client_id').strip()
    client_secret = request.form.get('client_secret').strip()
    session['client_id'] = client_id
    session['client_secret'] = client_secret
    
    redirect_uri = request.url_root.replace('http://', 'https://').rstrip('/') + 'callback'
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