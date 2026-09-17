import os
import time
import requests
from flask import Flask, request, jsonify, render_template_string
from playwright.sync_api import sync_playwright

app = Flask(__name__)

SESSION = {
    "sp_dc": None,
    "access_token": None,
    "expires_at": 0
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>In-Car Lyrics</title>
    <style>
        body { background: #121212; color: white; font-family: -apple-system, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .login-box { background: #282828; padding: 2rem; border-radius: 8px; text-align: center; width: 80%; max-width: 350px; }
        input { display: block; margin: 15px auto; padding: 12px; width: 85%; border-radius: 4px; border: none; font-size: 16px; background: #333; color: white;}
        button { background: #1DB954; color: white; border: none; padding: 12px 20px; border-radius: 20px; font-weight: bold; cursor: pointer; width: 93%; font-size: 16px;}
        #lyrics-container { display: none; width: 100%; height: 100vh; overflow: hidden; position: relative; text-align: center; flex-direction: column;}
        #track-header { background: #000; padding: 20px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5); z-index: 10;}
        #track-title { color: #1DB954; margin: 0; font-size: 24px;}
        #track-artist { color: #b3b3b3; margin: 5px 0 0 0; font-size: 16px;}
        #lyrics-scroll { flex-grow: 1; overflow-y: auto; padding: 50px 20px; padding-bottom: 50vh; }
        .lyric-line { font-size: 24px; color: #555; margin: 20px 0; transition: all 0.3s ease; }
        .active-line { color: #fff; font-size: 32px; font-weight: bold; }
    </style>
</head>
<body>

    <div id="login-ui" class="login-box">
        <h2 style="color: #1DB954;">Headless Auth</h2>
        <input type="text" id="user" placeholder="Spotify Email or Username" />
        <input type="password" id="pass" placeholder="Password" />
        <button onclick="doLogin()">Start Engine</button>
        <p id="status" style="color: #b3b3b3; font-size: 14px; margin-top: 15px;"></p>
    </div>

    <div id="lyrics-container">
        <div id="track-header">
            <h3 id="track-title">Waiting for music...</h3>
            <p id="track-artist"></p>
        </div>
        <div id="lyrics-scroll"></div>
    </div>

    <script>
        async function doLogin() {
            document.getElementById('status').innerText = 'Booting headless browser... (Takes ~10-15s)';
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    u: document.getElementById('user').value,
                    p: document.getElementById('pass').value
                })
            });
            
            const data = await res.json();
            
            if(data.success) {
                document.getElementById('login-ui').style.display = 'none';
                document.getElementById('lyrics-container').style.display = 'flex';
                setInterval(pollLyrics, 2000);
            } else {
                document.getElementById('status').innerText = 'Error: ' + data.error;
            }
        }

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
                        
                        data.lines.forEach((line, index) => {
                            const div = document.createElement('div');
                            div.className = 'lyric-line';
                            div.innerText = line.words;
                            div.dataset.time = line.startTimeMs;
                            scrollBox.appendChild(div);
                        });
                    }

                    let activeIndex = -1;
                    const lines = document.getElementsByClassName('lyric-line');
                    for (let i = 0; i < lines.length; i++) {
                        if (data.progressMs >= parseInt(lines[i].dataset.time)) {
                            activeIndex = i;
                        }
                    }
                    
                    for (let i = 0; i < lines.length; i++) {
                        if (i === activeIndex) {
                            if (!lines[i].classList.contains('active-line')) {
                                lines[i].classList.add('active-line');
                                lines[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                        } else {
                            lines[i].classList.remove('active-line');
                        }
                    }
                }
            } catch(e) {
                console.error(e);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
    creds = request.json
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            page = context.new_page()
            
            page.goto("https://accounts.spotify.com/en/login")
            page.fill("#login-username", creds.get('u'))
            page.fill("#login-password", creds.get('p'))
            page.click("#login-button")
            
            page.wait_for_url("https://open.spotify.com/**", timeout=15000)
            
            cookies = context.cookies()
            sp_dc = next((c['value'] for c in cookies if c['name'] == 'sp_dc'), None)
            browser.close()
            
            if sp_dc:
                SESSION['sp_dc'] = sp_dc
                SESSION['expires_at'] = 0 
                return jsonify({"success": True})
            return jsonify({"success": False, "error": "Login blocked or wrong password."})
                
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def get_access_token():
    if time.time() < SESSION['expires_at']:
        return SESSION['access_token']
        
    res = requests.get(
        "https://open.spotify.com/get_access_token?reason=transport&productType=web_player",
        headers={"Cookie": f"sp_dc={SESSION['sp_dc']}", "User-Agent": "Mozilla/5.0"}
    ).json()
    
    SESSION['access_token'] = res.get('accessToken')
    SESSION['expires_at'] = time.time() + (res.get('accessTokenExpirationTimestampMs', 300000) / 1000) - 60
    return SESSION['access_token']

@app.route('/api/now-playing')
def now_playing():
    if not SESSION['sp_dc']:
        return jsonify({"isPlaying": False, "error": "No session active."})
        
    try:
        token = get_access_token()
        
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
        
        lyrics_res = requests.get(
            f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}?format=json&market=from_token",
            headers={"Authorization": f"Bearer {token}", "App-Platform": "WebPlayer"}
        )
        
        lines = []
        if lyrics_res.ok:
            lines = lyrics_res.json().get('lyrics', {}).get('lines', [])
            
        return jsonify({
            "isPlaying": player.get('is_playing', False),
            "progressMs": player.get('progress_ms', 0),
            "title": player['item']['name'],
            "artist": ", ".join([a['name'] for a in player['item']['artists']]),
            "trackId": track_id,
            "lines": lines
        })
    except Exception as e:
        return jsonify({"isPlaying": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)