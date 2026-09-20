import os
import time
import requests
import urllib.parse
import base64
import re
from flask import Flask, request, jsonify, render_template_string, redirect, session, make_response

app = Flask(__name__)
app.secret_key = "super_secret_car_lyrics_key"

# Tiny silent looping mp4 used as an iOS "no-sleep" fallback (Wake Lock API
# isn't available on iOS Safari / older iOS versions). Generated locally,
# 2x2px, ~1s, silent audio track so autoplay-muted rules are happy.
NOSLEEP_VIDEO_B64 = "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAwJtZGF03gIATGF2YzYxLjE5LjEwMQACMEAOAAACrQYF//+p3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE2NCByMzEwOCAzMWUxOWY5IC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAyMyAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTEgbG9va2FoZWFkX3RocmVhZHM9MSBzbGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0wIGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0zIGJfcHlyYW1pZD0yIGJfYWRhcHQ9MSBiX2JpYXM9MCBkaXJlY3Q9MSB3ZWlnaHRiPTEgb3Blbl9nb3A9MCB3ZWlnaHRwPTIga2V5aW50PTI1MCBrZXlpbnRfbWluPTEgc2NlbmVjdXQ9NDAgaW50cmFfcmVmcmVzaD0wIHJjX2xvb2thaGVhZD00MCByYz1jcmYgbWJ0cmVlPTEgY3JmPTIzLjAgcWNvbXA9MC42MCBxcG1pbj0wIHFwbWF4PTY5IHFwc3RlcD00IGlwX3JhdGlvPTEuNDAgYXE9MToxLjAwAIAAAAAQZYiEABX//vfJ78Cm69vfgQEYIAcBGCAHARggBwEYIAcBGCAHARggBwEYIAcBGCAHAAAFg21vb3YAAABsbXZoZAAAAAAAAAAAAAAAAAAAA+gAAAPoAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAJBdHJhawAAAFx0a2hkAAAAAwAAAAAAAAAAAAAAAQAAAAAAAAPoAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAACAAAAAgAAAAAAJGVkdHMAAAAcZWxzdAAAAAAAAAABAAAD6AAAAAAAAQAAAAABuW1kaWEAAAAgbWRoZAAAAAAAAAAAAAAAAAAAQAAAAEAAVcQAAAAAAC1oZGxyAAAAAAAAAAB2aWRlAAAAAAAAAAAAAAAAVmlkZW9IYW5kbGVyAAAAAWRtaW5mAAAAFHZtaGQAAAABAAAAAAAAAAAAAAAkZGluZgAAABxkcmVmAAAAAAAAAAEAAAAMdXJsIAAAAAEAAAEkc3RibAAAAMBzdHNkAAAAAAAAAAEAAACwYXZjMQAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAACAAIASAAAAEgAAAAAAAAAARVMYXZjNjEuMTkuMTAxIGxpYngyNjQAAAAAAAAAAAAAABj//wAAADZhdmNDAWQACv/hABlnZAAKrNlfiIjARAAAAwAEAAADAAg8SJZYAQAGaOvjyyLA/fj4AAAAABBwYXNwAAAAAQAAAAEAAAAUYnRydAAAAAAAABYoAAAAAAAAABhzdHRzAAAAAAAAAAEAAAABAABAAAAAABxzdHNjAAAAAAAAAAEAAAABAAAAAQAAAAEAAAAUc3RzegAAAAAAAALFAAAAAQAAABRzdGNvAAAAAAAAAAEAAABFAAACbXRyYWsAAABcdGtoZAAAAAMAAAAAAAAAAAAAAAIAAAAAAAAD6AAAAAAAAAAAAAAAAQEAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAACRlZHRzAAAAHGVsc3QAAAAAAAAAAQAAA+gAAAQAAAEAAAAAAeVtZGlhAAAAIG1kaGQAAAAAAAAAAAAAAAAAAB9AAAAjQFXEAAAAAAAtaGRscgAAAAAAAAAAc291bgAAAAAAAAAAAAAAAFNvdW5kSGFuZGxlcgAAAAGQbWluZgAAABBzbWhkAAAAAAAAAAAAAAAkZGluZgAAABxkcmVmAAAAAAAAAAEAAAAMdXJsIAAAAAEAAAFUc3RibAAAAH5zdHNkAAAAAAAAAAEAAABubXA0YQAAAAAAAAABAAAAAAAAAAAAAQAQAAAAAB9AAAAAAAA2ZXNkcwAAAAADgICAJQACAASAgIAXQBUAAAAAALuAAAABdwWAgIAFFYhW5QAGgICAAQIAAAAUYnRydAAAAAAAALuAAAABdwAAACBzdHRzAAAAAAAAAAIAAAAIAAAEAAAAAAEAAANAAAAAKHN0c2MAAAAAAAAAAgAAAAEAAAABAAAAAQAAAAIAAAAIAAAAAQAAADhzdHN6AAAAAAAAAAAAAAAJAAAAFQAAAAQAAAAEAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAAGHN0Y28AAAAAAAAAAgAAADAAAAMKAAAAGnNncGQBAAAAcm9sbAAAAAIAAAAB//8AAAAcc2JncAAAAAByb2xsAAAAAQAAAAkAAAABAAAAYXVkdGEAAABZbWV0YQAAAAAAAAAhaGRscgAAAAAAAAAAbWRpcmFwcGwAAAAAAAAAAAAAAAAsaWxzdAAAACSpdG9vAAAAHGRhdGEAAAABAAAAAExhdmY2MS43LjEwMw=="

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Spotify</title>
    <!-- Geometric All-Caps Premium Font. Every weight actually used
         anywhere on the site (pills, buttons, both lyric lines) is
         requested here as its own static face so nothing on the page ever
         falls back to a browser-synthesized weight or a different
         fallback typeface. -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&display=block" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.0/color-thief.umd.js"></script>
    <style>
        * { -webkit-tap-highlight-color: transparent; }
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
            transition: background-color 2.2s cubic-bezier(0.4, 0, 0.2, 1),
                        opacity 0.2s ease;
        }

        /* Nothing is shown until the real webfont is confirmed loaded (or
           a short timeout passes), so no element can ever paint in a
           fallback typeface that looks different from the rest of the
           page. See the inline script right after <body>. */
        body:not(.fonts-ready) { opacity: 0; }

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
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
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
            width: 94vw;
            height: calc(100dvh - 96px);
            position: relative;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 3vh;
            z-index: 10;
            box-sizing: border-box;
        }

        .lyric-line {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 1em;
        }

        .lyric-inner {
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            padding: 0 10px;
            max-width: 100%;
            line-height: 1.25;
            opacity: 0;
            will-change: opacity, font-size;
            transition: opacity 0.32s cubic-bezier(0.4, 0, 0.2, 1),
                        font-size 0.32s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .adjacent-line .lyric-inner {
            font-weight: 600;
        }

        .active-line .lyric-inner {
            font-weight: 900;
            text-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        #controls-bar {
            position: absolute;
            bottom: max(24px, env(safe-area-inset-bottom));
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 20;
            background: rgba(0, 0, 0, 0.3);
            padding: 20px 30px 12px;
            border-radius: 40px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            width: min(420px, 82vw);
            box-sizing: border-box;
        }

        /* Progress bar sits right along the top edge of the pill, curving
           with it, so it reads as part of the pill's border rather than a
           separate element floating inside it. */
        #progress-track {
            position: absolute;
            top: 0;
            left: 14px;
            right: 14px;
            height: 20px;
            display: flex;
            align-items: center;
            cursor: pointer;
            touch-action: none;
            z-index: 21;
        }

        #progress-track::before {
            content: '';
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            height: 3px;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.22);
            border-radius: 3px;
        }

        #progress-fill {
            position: absolute;
            left: 0;
            top: 50%;
            height: 3px;
            transform: translateY(-50%);
            width: 0%;
            background: #1DB954;
            border-radius: 3px;
            transition: width 0.1s linear;
        }

        #progress-track.seeking #progress-fill,
        #progress-track.seeking #progress-thumb {
            transition: none;
        }

        #progress-thumb {
            position: absolute;
            top: 50%;
            left: 0%;
            width: 11px;
            height: 11px;
            border-radius: 50%;
            background: #fff;
            transform: translate(-50%, -50%);
            box-shadow: 0 1px 4px rgba(0,0,0,0.4);
            transition: left 0.1s linear, opacity 0.15s ease;
            opacity: 0;
        }

        #controls-bar:hover #progress-thumb,
        #progress-track.seeking #progress-thumb {
            opacity: 1;
        }

        #now-playing-title {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            padding: 0 4px;
            margin-bottom: 6px;
            height: 18px;
        }

        #now-playing-title-inner {
            color: rgba(255, 255, 255, 0.85);
            font-weight: 700;
            white-space: nowrap;
            letter-spacing: 0.2px;
            line-height: 1;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
        }

        #controls-row {
            display: flex;
            gap: 30px;
            align-items: center;
            justify-content: center;
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
            transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.15s ease;
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
    <script>
        // Reveal the page only once the Montserrat weights we use are
        // actually loaded (or after a short safety timeout), so the pills,
        // buttons and lyrics are always painted in the same real font
        // instead of a fallback that briefly looks different.
        (function () {
            function reveal() { document.body.classList.add('fonts-ready'); }
            if (document.fonts && document.fonts.ready) {
                Promise.race([
                    Promise.all([
                        document.fonts.load("700 16px 'Montserrat'"),
                        document.fonts.load("900 16px 'Montserrat'"),
                        document.fonts.ready
                    ]),
                    new Promise(function (r) { setTimeout(r, 700); })
                ]).then(reveal, reveal);
            } else {
                reveal();
            }
        })();
    </script>

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
        <div id="progress-track">
            <div id="progress-fill"></div>
            <div id="progress-thumb"></div>
        </div>
        <div id="now-playing-title"><span id="now-playing-title-inner"></span></div>
        <div id="controls-row">
            <button class="control-btn" onclick="sendControl('previous')">
                <svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
            </button>
            <button class="control-btn" onclick="togglePlayPause()">
                <svg viewBox="0 0 24 24" id="play-pause-icon"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>
            <button class="control-btn" onclick="sendControl('next')">
                <svg viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
            </button>
        </div>
    </div>

    <script>
        const colorThief = new ColorThief();
        const NOSLEEP_SRC = "data:video/mp4;base64,{{ nosleep_video }}";

        let cachedTrackId = "";
        let parsedLines = [];
        let wakeLock = null;
        let noSleepVideo = null;

        let serverProgress = 0;
        let serverTimestamp = 0;
        let isPlaying = false;
        let lastActiveIndex = -2;
        let trackDurationMs = 0;
        let isSeeking = false;
        let seekPositionMs = 0;

        // ---------- Opacity targets per slot ----------
        const OPACITY_ACTIVE = 1;
        const OPACITY_ADJACENT = 0.35;

        // ---------- Wake Lock (with iOS fallback) ----------
        async function requestWakeLock() {
            try {
                if ('wakeLock' in navigator) {
                    if (!wakeLock) {
                        wakeLock = await navigator.wakeLock.request('screen');
                        wakeLock.addEventListener('release', () => { wakeLock = null; });
                    }
                    return;
                }
            } catch (err) {
                // ignore, fall through to video fallback
            }
            startNoSleepFallback();
        }

        function startNoSleepFallback() {
            if (noSleepVideo) {
                noSleepVideo.play().catch(() => {});
                return;
            }
            const video = document.createElement('video');
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');
            video.muted = true;
            video.loop = true;
            video.style.position = 'fixed';
            video.style.top = '0';
            video.style.left = '0';
            video.style.width = '1px';
            video.style.height = '1px';
            video.style.opacity = '0';
            video.style.pointerEvents = 'none';
            video.src = NOSLEEP_SRC;
            document.body.appendChild(video);
            noSleepVideo = video;
            video.play().catch(() => {});
        }

        function tryReacquireWakeLock() {
            requestWakeLock();
        }

        window.addEventListener('load', requestWakeLock);
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') tryReacquireWakeLock();
        });
        document.body.addEventListener('click', requestWakeLock);
        document.body.addEventListener('touchstart', requestWakeLock, { passive: true });
        window.addEventListener('orientationchange', () => setTimeout(tryReacquireWakeLock, 350));
        if (screen.orientation && screen.orientation.addEventListener) {
            screen.orientation.addEventListener('change', () => setTimeout(tryReacquireWakeLock, 350));
        }

        window.addEventListener('beforeunload', () => {
            navigator.sendBeacon('/logout');
        });

        // ---------- Playback controls ----------
        // Optimistic play/pause: the button flips instantly on click instead
        // of waiting on a network round trip, and we tell the server the
        // exact target state (no extra state-read call, no race). Polling
        // is told to briefly trust the optimistic state so a slightly-stale
        // response from Spotify can't flicker the icon back before the
        // change has actually propagated.
        let optimisticIsPlaying = null;
        let optimisticExpires = 0;

        async function sendControl(action) {
            requestWakeLock();
            try {
                const res = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                const data = await res.json().catch(() => ({}));
                if (!data.success) {
                    // Server confirmed the action failed - drop the
                    // optimistic override so the next poll shows reality.
                    optimisticIsPlaying = null;
                    optimisticExpires = 0;
                }
            } catch (e) {
                optimisticIsPlaying = null;
                optimisticExpires = 0;
            }
            pollServer(true);
        }

        function togglePlayPause() {
            const target = !isPlaying;
            isPlaying = target;
            optimisticIsPlaying = target;
            optimisticExpires = performance.now() + 2500;
            updatePlayPauseIcon();
            sendControl(target ? 'play' : 'pause');
        }

        function updatePlayPauseIcon() {
            const icon = document.getElementById('play-pause-icon');
            icon.innerHTML = isPlaying
                ? '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>'
                : '<path d="M8 5v14l11-7z"/>';
        }

        // ---------- Auto-fit sizing ----------
        // Sizes are computed synchronously from (text, container width) using
        // an offscreen canvas measurement - no live-DOM binary search, no
        // reflow loop, no dependency on transition/opacity state. Same text
        // always yields the same size, so there is no race where a line
        // briefly renders at the wrong size mid-transition.
        const containerEl = document.getElementById('lyrics-container');
        const ACTIVE_MAX = 100, ACTIVE_MIN = 22;
        const ADJACENT_MAX = 40, ADJACENT_MIN = 14;
        const ACTIVE_WEIGHT = 900, ADJACENT_WEIGHT = 600;
        const REF_SIZE = 100;

        const measureCanvas = document.createElement('canvas');
        const measureCtx = measureCanvas.getContext('2d');
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => { refitCurrentLines(); });
        }

        function measureWidthAtRef(text, weight) {
            measureCtx.font = `${weight} ${REF_SIZE}px 'Montserrat', sans-serif`;
            return measureCtx.measureText(text).width || 1;
        }

        function computeFontSize(text, isActive) {
            const maxSize = isActive ? ACTIVE_MAX : ADJACENT_MAX;
            const minSize = isActive ? ACTIVE_MIN : ADJACENT_MIN;
            if (!text) return maxSize;

            const weight = isActive ? ACTIVE_WEIGHT : ADJACENT_WEIGHT;
            const maxWidth = containerEl.clientWidth * 0.94;
            // Longer lines are allowed to wrap to two physical lines, so give
            // width-based sizing a little headroom instead of forcing every
            // line onto one row at a tiny size.
            const wrapAllowance = text.length > 24 ? 1.55 : 1;

            const refWidth = measureWidthAtRef(text, weight);
            let size = (maxWidth * wrapAllowance / refWidth) * REF_SIZE;

            // Cap by available height too (roughly, assuming up to 2 wrapped
            // lines at this font size).
            const maxHeight = containerEl.clientHeight * (isActive ? 0.46 : 0.22);
            const lines = wrapAllowance > 1 ? 2 : 1;
            const heightCap = maxHeight / (lines * 1.25);
            size = Math.min(size, heightCap);

            size = Math.min(size, maxSize);
            size = Math.max(size, minSize);
            return Math.round(size);
        }

        // ---------- Coordinated crossfade text swap ----------
        // All three slots are computed together before anything is touched,
        // so prev/active/next never briefly show mismatched sizes.
        const FADE_MS = 160;
        const slots = {
            'prev-line': { inner: document.querySelector('#prev-line .lyric-inner'), opacity: OPACITY_ADJACENT, isActive: false },
            'active-line': { inner: document.querySelector('#active-line .lyric-inner'), opacity: OPACITY_ACTIVE, isActive: true },
            'next-line': { inner: document.querySelector('#next-line .lyric-inner'), opacity: OPACITY_ADJACENT, isActive: false }
        };

        function applyLines(prevText, activeText, nextText) {
            setSlot(slots['prev-line'], prevText || '');
            setSlot(slots['active-line'], activeText || '');
            setSlot(slots['next-line'], nextText || '');
        }

        function setSlot(slot, text) {
            const inner = slot.inner;
            if (inner.dataset.text === text) return;
            const hadContent = !!inner.dataset.text;
            inner.dataset.text = text;

            const size = computeFontSize(text, slot.isActive);

            clearTimeout(inner._fadeTimer);
            if (!hadContent && !inner.textContent) {
                // Nothing was showing yet - fade straight in, no need to
                // fade out first.
                inner.textContent = text;
                inner.style.fontSize = size + 'px';
                requestAnimationFrame(() => {
                    inner.style.opacity = text ? String(slot.opacity) : '0';
                });
                return;
            }

            inner.style.opacity = '0';
            inner._fadeTimer = setTimeout(() => {
                inner.textContent = text;
                inner.style.fontSize = size + 'px';
                requestAnimationFrame(() => {
                    inner.style.opacity = text ? String(slot.opacity) : '0';
                });
            }, FADE_MS);
        }

        function refitCurrentLines() {
            Object.values(slots).forEach(slot => {
                const text = slot.inner.dataset.text || '';
                if (!text) return;
                slot.inner.style.fontSize = computeFontSize(text, slot.isActive) + 'px';
            });
        }

        let resizeTimer = null;
        function scheduleRefit() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => { refitCurrentLines(); fitTitle(); }, 120);
            // Mobile browsers can report stale dimensions right after a
            // rotation event, so double-check shortly after too.
            setTimeout(() => { refitCurrentLines(); fitTitle(); }, 400);
        }
        window.addEventListener('resize', scheduleRefit);
        window.addEventListener('orientationchange', scheduleRefit);

        // ---------- Now-playing title: always sized to fit the pill ----------
        // Same idea as the lyric auto-fit: measure the text once at a
        // reference size and scale down to the exact width available,
        // never wrapping and never overflowing the pill.
        const titleEl = document.getElementById('now-playing-title');
        const titleInnerEl = document.getElementById('now-playing-title-inner');
        const TITLE_MAX = 15, TITLE_MIN = 7;
        let currentTitleText = '';

        function computeTitleFontSize(text) {
            if (!text) return TITLE_MAX;
            measureCtx.font = `700 ${REF_SIZE}px 'Montserrat', sans-serif`;
            const refWidth = measureCtx.measureText(text).width || 1;
            const maxWidth = titleEl.clientWidth * 0.98;
            let size = (maxWidth / refWidth) * REF_SIZE;
            size = Math.min(size, TITLE_MAX);
            size = Math.max(size, TITLE_MIN);
            return Math.round(size * 10) / 10;
        }

        function fitTitle() {
            if (!currentTitleText) return;
            titleInnerEl.style.fontSize = computeTitleFontSize(currentTitleText) + 'px';
        }

        function setTitle(title, artist) {
            const text = artist ? `${title} — ${artist}` : title;
            if (text === currentTitleText) return;
            currentTitleText = text;
            titleInnerEl.textContent = text;
            titleInnerEl.style.fontSize = computeTitleFontSize(text) + 'px';
        }

        // ---------- Progress bar / seek ----------
        // A thin bar running along the top edge of the controls pill.
        // Dragging (or a single click/tap) anywhere on it seeks to that
        // point in the track. While the server round trip for the seek is
        // in flight, the bar is driven purely from the local drag position
        // so it never jumps or lags behind the finger/cursor.
        const progressTrack = document.getElementById('progress-track');
        const progressFill = document.getElementById('progress-fill');
        const progressThumb = document.getElementById('progress-thumb');

        function setProgressVisual(ratio) {
            const pct = Math.min(100, Math.max(0, ratio * 100));
            progressFill.style.width = pct + '%';
            progressThumb.style.left = pct + '%';
        }

        function ratioFromEvent(e) {
            const rect = progressTrack.getBoundingClientRect();
            const clientX = e.touches && e.touches.length ? e.touches[0].clientX : e.clientX;
            const x = clientX - rect.left;
            return Math.min(1, Math.max(0, rect.width > 0 ? x / rect.width : 0));
        }

        function updateSeekFromEvent(e) {
            if (!trackDurationMs) return;
            const ratio = ratioFromEvent(e);
            setProgressVisual(ratio);
            seekPositionMs = Math.round(ratio * trackDurationMs);
        }

        function startSeek(e) {
            if (!trackDurationMs) return;
            isSeeking = true;
            progressTrack.classList.add('seeking');
            updateSeekFromEvent(e);
            e.preventDefault();
        }

        function endSeek() {
            if (!isSeeking) return;
            isSeeking = false;
            progressTrack.classList.remove('seeking');
            serverProgress = seekPositionMs;
            serverTimestamp = performance.now();
            sendSeek(seekPositionMs);
        }

        async function sendSeek(positionMs) {
            requestWakeLock();
            try {
                await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'seek', positionMs: positionMs })
                });
            } catch (e) {
                // ignore - next poll will resync to real server position
            }
            pollServer(true);
        }

        progressTrack.addEventListener('mousedown', startSeek);
        progressTrack.addEventListener('touchstart', startSeek, { passive: false });
        window.addEventListener('mousemove', (e) => { if (isSeeking) updateSeekFromEvent(e); });
        window.addEventListener('touchmove', (e) => { if (isSeeking) { updateSeekFromEvent(e); e.preventDefault(); } }, { passive: false });
        window.addEventListener('mouseup', endSeek);
        window.addEventListener('touchend', endSeek);
        window.addEventListener('touchcancel', endSeek);

        // ---------- Polling (guarded against overlap / out-of-order) ----------
        let pollInFlight = false;
        let pollSeq = 0;
        let missCount = 0;

        async function pollServer(force) {
            if (pollInFlight && !force) return;
            pollInFlight = true;
            const mySeq = ++pollSeq;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 6000);

            try {
                const fetchStart = performance.now();
                const res = await fetch(`/api/now-playing?t=${Date.now()}`, { signal: controller.signal });
                const data = await res.json();
                const fetchEnd = performance.now();

                // A newer request already resolved; discard this stale one.
                if (mySeq !== pollSeq) return;

                const networkLatency = (fetchEnd - fetchStart) / 2;
                missCount = 0;

                // Reconcile server truth with an in-flight optimistic
                // play/pause: trust the optimistic value until either the
                // server confirms it or the grace window runs out.
                let effectiveIsPlaying = data.isPlaying;
                if (optimisticIsPlaying !== null) {
                    if (data.isPlaying === optimisticIsPlaying || performance.now() > optimisticExpires) {
                        optimisticIsPlaying = null;
                        optimisticExpires = 0;
                    } else {
                        effectiveIsPlaying = optimisticIsPlaying;
                    }
                }

                if (effectiveIsPlaying && data.trackId) {
                    isPlaying = true;
                    if (!isSeeking) {
                        serverProgress = data.progressMs;
                        serverTimestamp = performance.now() - networkLatency;
                    }
                    trackDurationMs = data.durationMs || 0;
                    updatePlayPauseIcon();
                    setTitle(data.title, data.artist);

                    if (cachedTrackId !== data.trackId) {
                        cachedTrackId = data.trackId;
                        parsedLines = data.lines || [];
                        lastActiveIndex = -2;

                        applyLines('', '', '');

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
                                } catch (e) {}
                            };
                            img.src = data.albumArt;
                        } else {
                            document.body.style.backgroundColor = '#121212';
                        }
                    }
                } else if (data.trackId) {
                    // Paused, but a track is still loaded - freeze the
                    // lyrics on screen exactly as they are (matches how
                    // Spotify's own lyrics view behaves on pause) instead
                    // of blanking the screen.
                    isPlaying = false;
                    if (!isSeeking) {
                        serverProgress = data.progressMs;
                        serverTimestamp = performance.now() - networkLatency;
                    }
                    trackDurationMs = data.durationMs || 0;
                    updatePlayPauseIcon();
                    setTitle(data.title, data.artist);
                    cachedTrackId = data.trackId;
                } else {
                    // Nothing loaded at all.
                    isPlaying = false;
                    updatePlayPauseIcon();
                    applyLines('', '', '');
                    lastActiveIndex = -1;
                    cachedTrackId = "";
                    trackDurationMs = 0;
                    currentTitleText = '';
                    titleInnerEl.textContent = '';
                    if (!isSeeking) setProgressVisual(0);
                }
            } catch (e) {
                // Network hiccup: count misses, and if we've been stuck for a
                // while force an immediate re-check rather than silently
                // sitting on stale state.
                missCount++;
                if (missCount >= 2) setTimeout(() => pollServer(true), 200);
            } finally {
                clearTimeout(timeoutId);
                if (mySeq === pollSeq) pollInFlight = false;
            }
        }

        setInterval(() => pollServer(false), 700);
        pollServer(true);

        function animationLoop() {
            const currentProgress = isPlaying
                ? serverProgress + (performance.now() - serverTimestamp)
                : serverProgress;

            // Drive the progress bar every frame for a perfectly smooth
            // sweep, except while the user is actively dragging it - then
            // their own touch/drag position is the source of truth.
            if (!isSeeking && trackDurationMs > 0) {
                setProgressVisual(currentProgress / trackDurationMs);
            }

            if (isPlaying && parsedLines.length > 0) {
                let activeIndex = -1;
                for (let i = 0; i < parsedLines.length; i++) {
                    if (parsedLines[i].startTimeMs <= currentProgress) {
                        activeIndex = i;
                    } else {
                        break;
                    }
                }

                if (activeIndex !== lastActiveIndex) {
                    lastActiveIndex = activeIndex;

                    const prevText = activeIndex > 0 ? parsedLines[activeIndex - 1].words : "";
                    const activeText = activeIndex >= 0 ? parsedLines[activeIndex].words : "";
                    const nextText = activeIndex + 1 < parsedLines.length ? parsedLines[activeIndex + 1].words : "";

                    applyLines(prevText, activeText, nextText);
                }
            }
            // When paused, intentionally do nothing else here: the lyric
            // lines stay exactly as they were, frozen, rather than
            // disappearing.
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
    return render_template_string(
        HTML_TEMPLATE,
        is_authed=is_authed,
        redirect_uri=redirect_uri,
        error=error_msg,
        nosleep_video=NOSLEEP_VIDEO_B64
    )

@app.route('/favicon.ico')
def favicon():
    return '', 204

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

    scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state"

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
            data={"grant_type": "refresh_token", "refresh_token": session.get('refresh_token', '')},
            timeout=6
        )

        if res.ok:
            data = res.json()
            session['access_token'] = data.get('access_token')
            session['expires_at'] = time.time() + data.get('expires_in', 3600) - 60
            return session['access_token']
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Lyrics: single source (LRCLIB). No secondary fallback provider - if LRCLIB
# has nothing synced for the track, the client just shows a blank lyrics
# screen tinted with the album color.
# ---------------------------------------------------------------------------

MAX_LINE_CHARS = 42          # roughly what fits on one comfortable display line
MIN_CHUNK_MS = 500           # floor for an interpolated sub-line's duration
LAST_LINE_MS_PER_CHAR = 70   # fallback pacing estimate for the very last line
LAST_LINE_MIN_MS = 1800

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

def wrap_words(text, max_chars):
    """Greedy word-wrap a single lyric line into chunks that each fit
    comfortably on one display line."""
    words = text.split()
    if not words:
        return [text]
    chunks = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            chunks.append(current)
            current = w
    if current:
        chunks.append(current)
    return chunks or [text]

def split_long_lines(lines, max_chars=MAX_LINE_CHARS):
    """Take LRCLIB's line-level synced lyrics and, for any line that's much
    longer than a comfortable display line, split it into several timed
    sub-lines with proportionally interpolated timestamps. Short lines pass
    through untouched."""
    if not lines:
        return []

    result = []
    n = len(lines)
    for i, ln in enumerate(lines):
        start = ln['startTimeMs']
        text = ln['words']

        if i + 1 < n:
            end = max(lines[i + 1]['startTimeMs'], start + MIN_CHUNK_MS)
        else:
            end = start + max(LAST_LINE_MIN_MS, len(text) * LAST_LINE_MS_PER_CHAR)

        if len(text) <= max_chars:
            result.append({"startTimeMs": start, "words": text})
            continue

        chunks = wrap_words(text, max_chars)
        if len(chunks) == 1:
            result.append({"startTimeMs": start, "words": chunks[0]})
            continue

        duration = max(end - start, MIN_CHUNK_MS * len(chunks))
        total_len = sum(len(c) for c in chunks) or 1
        cursor = start
        for idx, chunk in enumerate(chunks):
            result.append({"startTimeMs": cursor, "words": chunk})
            if idx < len(chunks) - 1:
                proportion = len(chunk) / total_len
                chunk_duration = max(int(duration * proportion), MIN_CHUNK_MS)
                cursor += chunk_duration

    return result

def fetch_synced_lyrics(track_name, artist_name):
    cleaned_name = re.sub(
        r'\s*[\(\[].*?(feat\.|ft\.|remaster|version|mix).*?[\)\]]',
        '', track_name, flags=re.IGNORECASE
    )
    cleaned_name = re.sub(
        r'\s*-.*?(Remaster|Live|Mono|Stereo).*',
        '', cleaned_name, flags=re.IGNORECASE
    ).strip()

    try:
        search_res = requests.get(
            "https://lrclib.net/api/search",
            params={"q": f"{cleaned_name} {artist_name}"},
            headers={"User-Agent": "InCarLyricsApp/1.0"},
            timeout=4
        )
        if search_res.ok:
            search_data = search_res.json()
            if isinstance(search_data, list):
                for track in search_data:
                    if isinstance(track, dict) and track.get('syncedLyrics'):
                        raw_lines = parse_lrc(track['syncedLyrics'])
                        return split_long_lines(raw_lines)
    except Exception:
        pass

    return []


@app.route('/api/control', methods=['POST'])
def control():
    token = get_valid_token()
    if not token:
        return jsonify({"success": False, "error": "Not logged in"})

    payload = request.get_json(silent=True) or {}
    action = payload.get('action')

    try:
        if action in ('play', 'pause'):
            # The client already knows whether playback is playing or paused
            # from its own polling, so it tells us the target state directly.
            # This avoids an extra GET /me/player round trip (which also
            # needs a broader scope than reading currently-playing does) and
            # the staleness/race that round trip could introduce.
            res = requests.put(
                f"https://api.spotify.com/v1/me/player/{action}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if res.status_code in (200, 202, 204):
                return jsonify({"success": True})
            return jsonify({"success": False, "error": f"spotify_{res.status_code}"})

        elif action in ('next', 'previous'):
            res = requests.post(
                f"https://api.spotify.com/v1/me/player/{action}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if res.status_code in (200, 202, 204):
                return jsonify({"success": True})
            return jsonify({"success": False, "error": f"spotify_{res.status_code}"})

        elif action == 'seek':
            position_ms = payload.get('positionMs')
            try:
                position_ms = max(0, int(position_ms))
            except (TypeError, ValueError):
                return jsonify({"success": False, "error": "bad_position"})
            res = requests.put(
                "https://api.spotify.com/v1/me/player/seek",
                params={"position_ms": position_ms},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if res.status_code in (200, 202, 204):
                return jsonify({"success": True})
            return jsonify({"success": False, "error": f"spotify_{res.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "error": "network_error"})

    return jsonify({"success": False, "error": "unknown_action"})

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

    lines = fetch_synced_lyrics(track_name, artist_name)
    duration_ms = item.get('duration_ms') or 0

    return jsonify({
        "isPlaying": player.get('is_playing', False),
        "progressMs": player.get('progress_ms', 0),
        "durationMs": duration_ms,
        "title": track_name,
        "artist": artist_name,
        "albumArt": album_art,
        "trackId": track_id,
        "lines": lines
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)