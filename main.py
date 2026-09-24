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
            white-space: nowrap;
            padding: 0 10px;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
            line-height: 1.15;
            opacity: 0;
            will-change: opacity, font-size;
            transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1),
                        font-size 0.2s cubic-bezier(0.4, 0, 0.2, 1);
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

        /* Progress indicator traces the whole perimeter of the pill as a
           border-like ring (SVG path matching the pill's own rounded-rect
           shape), rather than a bar across just the top edge. Filling
           starts at top-center and sweeps clockwise all the way around. */
        #progress-ring {
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
            display: block;
            z-index: 21;
            overflow: visible;
        }

        #progress-hit {
            pointer-events: stroke;
            cursor: pointer;
            touch-action: none;
        }

        #progress-thumb {
            opacity: 0;
            transition: opacity 0.15s ease;
        }

        #controls-bar:hover #progress-thumb,
        #progress-ring.seeking #progress-thumb {
            opacity: 1;
        }

        #progress-track-fill {
            transition: stroke-dasharray 0.1s linear;
        }

        #progress-ring.seeking #progress-track-fill {
            transition: none;
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

        /* When the title is too long to fully fit even at the smallest
           readable size, it left-aligns and scrolls (marquee) instead of
           being permanently truncated with an ellipsis. */
        #now-playing-title.marquee-active {
            justify-content: flex-start;
        }

        #now-playing-title-inner {
            color: rgba(255, 255, 255, 0.85);
            font-weight: 700;
            white-space: nowrap;
            letter-spacing: 0.2px;
            line-height: 1;
            display: inline-block;
            flex-shrink: 0;
        }

        /* Static (non-marquee) state: the text already fits inside
           #now-playing-title (which itself clips via overflow:hidden), so
           a max-width/ellipsis pair here is only a last-resort safety net
           for a stray sub-pixel overflow, never the normal case. */
        #now-playing-title-inner:not(.marquee) {
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Marquee state: the clipping viewport is the outer
           #now-playing-title element. The inner span must NOT also clip
           its own overflow or truncate with an ellipsis - doing both at
           once is what previously made the title look like it was
           simultaneously "stuck" (clipped) and "juddering" (the transform
           animating underneath content that was already cut off). Here
           the inner span is left free to be exactly as wide as its full
           text and simply slides left across the fixed-width viewport. */
        #now-playing-title-inner.marquee {
            max-width: none;
            overflow: visible;
            text-overflow: clip;
            animation: marquee-scroll var(--marquee-duration, 6s) linear infinite;
            will-change: transform;
        }

        /* Song title vs. artist: two distinct weights/opacities instead
           of a plain em-dash separator, so the pair reads as "title, then
           who it's by" rather than one flat run of text. */
        .tt-song {
            color: rgba(255, 255, 255, 0.95);
            font-weight: 800;
        }
        .tt-sep {
            color: rgba(255, 255, 255, 0.3);
            font-weight: 600;
        }
        .tt-artist {
            color: rgba(255, 255, 255, 0.55);
            font-weight: 600;
        }

        /* One continuous left-moving pass across the whole hidden text,
           not a there-and-back oscillation: hold briefly at the start so
           the beginning is readable, travel once all the way to fully
           reveal the tail of the text, hold briefly there, then loop
           (an instant reset, same as any ticker/marquee - not a visible
           reverse). */
        @keyframes marquee-scroll {
            0%, 6%    { transform: translateX(0); }
            94%, 100% { transform: translateX(var(--marquee-distance, 0)); }
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
        <svg id="progress-ring" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#22e06a"></stop>
                    <stop offset="55%" stop-color="#1DB954"></stop>
                    <stop offset="100%" stop-color="#149c48"></stop>
                </linearGradient>
                <filter id="ringGlow" x="-60%" y="-60%" width="220%" height="220%">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="blur"></feGaussianBlur>
                    <feMerge>
                        <feMergeNode in="blur"></feMergeNode>
                        <feMergeNode in="SourceGraphic"></feMergeNode>
                    </feMerge>
                </filter>
                <filter id="thumbGlow" x="-150%" y="-150%" width="400%" height="400%">
                    <feDropShadow dx="0" dy="0" stdDeviation="2.2" flood-color="#1DB954" flood-opacity="0.9"></feDropShadow>
                </filter>
            </defs>
            <g id="progress-ring-group">
                <path id="progress-track-bg" fill="none" stroke="rgba(255,255,255,0.16)" stroke-width="3" stroke-linecap="round"></path>
                <path id="progress-track-fill" fill="none" stroke="url(#ringGradient)" stroke-width="3.5" stroke-linecap="round" filter="url(#ringGlow)"></path>
                <path id="progress-hit" fill="none" stroke="rgba(0,0,0,0.01)" stroke-width="26" stroke-linecap="round"></path>
                <circle id="progress-thumb" r="5.5" fill="#fff" filter="url(#thumbGlow)"></circle>
            </g>
        </svg>
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
        let seekGraceUntil = 0;

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
        const ACTIVE_MAX = 100, ACTIVE_MIN = 12;
        const ADJACENT_MAX = 40, ADJACENT_MIN = 9;
        const ACTIVE_WEIGHT = 900, ADJACENT_WEIGHT = 600;
        const REF_SIZE = 100;
        // Canvas measureText() has no idea the real element renders with
        // CSS letter-spacing - it measures raw glyph advances only. Left
        // uncorrected, the font size solved from that measurement is
        // systematically too large, so the real rendered line ends up
        // wider than its box and gets clipped with "...". Letter-spacing
        // in CSS is a fixed px add-on per character (it does not scale
        // with font-size), so it's subtracted from the available width
        // up front, before solving for size, rather than baked into the
        // canvas measurement itself.
        const LYRIC_LETTER_SPACING = 1.5; // px, matches body's letter-spacing
        const LYRIC_HPAD = 10;            // px, matches .lyric-inner's own padding
        const LYRIC_SAFETY = 8;           // px, extra margin against rounding

        const measureCanvas = document.createElement('canvas');
        const measureCtx = measureCanvas.getContext('2d');
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => { refitCurrentLines(); fitTitle(); layoutRing(); });
        }

        function measureWidthAtRef(text, weight) {
            measureCtx.font = `${weight} ${REF_SIZE}px 'Montserrat', sans-serif`;
            // The real element renders with `text-transform: uppercase`
            // (inherited from body), but the text handed to measureText()
            // here is the original mixed/lower-case source string. Capital
            // glyphs are almost always wider than their lowercase
            // counterparts, so measuring the raw string systematically
            // *underestimates* the true rendered width - the size solved
            // from that measurement then comes out too large and the real
            // (uppercase) line overflows and gets ellipsis-clipped, even
            // though the math "checked out" against the wrong string.
            // Measuring the upper-cased text is what the element actually
            // paints, so this is the fix, not a refinement.
            return measureCtx.measureText(text.toUpperCase()).width || 1;
        }

        // Every lyric line renders on exactly one physical line, however
        // short (a single word) or long it is - never wrapped to two or
        // three lines. Size is picked purely so the whole line's width
        // fits the available space; a one-line height cap keeps very long
        // lines from getting tall enough to clip vertically instead.
        // Returns both the chosen size and the hard pixel width budget it
        // was solved against, so callers can also verify against the real
        // live DOM afterwards (canvas measurement is a very close estimate,
        // not a guarantee - see fitTextToWidth below).
        function computeFontSize(text, isActive) {
            const maxSize = isActive ? ACTIVE_MAX : ADJACENT_MAX;
            const minSize = isActive ? ACTIVE_MIN : ADJACENT_MIN;
            const spacingExtra = (text || '').length * LYRIC_LETTER_SPACING;
            const rawMaxWidth = containerEl.clientWidth * 0.92 - LYRIC_HPAD * 2 - spacingExtra - LYRIC_SAFETY;
            const availWidth = Math.max(1, rawMaxWidth);
            if (!text) return { size: maxSize, availWidth };

            const weight = isActive ? ACTIVE_WEIGHT : ADJACENT_WEIGHT;
            const refWidth = measureWidthAtRef(text, weight);

            let size = (availWidth / refWidth) * REF_SIZE;

            // Cap by the vertical room one line is actually allotted, so a
            // short line at max size never grows tall enough to crowd its
            // neighbours.
            const maxHeight = containerEl.clientHeight * (isActive ? 0.30 : 0.16);
            const heightCap = maxHeight / 1.15;
            size = Math.min(size, heightCap);

            size = Math.min(size, maxSize);
            size = Math.max(size, minSize);
            return { size: Math.round(size), availWidth };
        }

        // Canvas pre-measurement gets very close but isn't pixel-exact
        // once real font hinting, subpixel rounding and the browser's own
        // uppercase-transform glyph substitution are all in play. Rather
        // than trust the estimate blindly (which is what kept producing
        // the "..." clipping even after correcting for letter-spacing and
        // case), the actual rendered element is measured right after the
        // estimate is applied, and nudged down a few times if it still
        // doesn't fit - a cheap, synchronous, no-extra-frame correction
        // against ground truth instead of a second formula to get wrong.
        // minSize is the normal, designed-for readable floor. If the
        // element still doesn't fit even there (a very long line on a very
        // narrow screen), it's allowed to keep shrinking past that floor
        // down to HARD_FLOOR_PX - a small, still-legible size is a much
        // better outcome than the line being ellipsis-clipped, which is
        // the exact symptom this whole pass exists to get rid of.
        const HARD_FLOOR_PX = 7;
        function fitTextToWidth(el, guessSize, minSize, availWidth) {
            // The element's own stylesheet rule transitions font-size
            // (so a genuine active<->adjacent size change fades smoothly
            // instead of snapping). But this loop can write font-size
            // several times in a row while forcing a synchronous layout
            // read (el.scrollWidth) between each write - and a layout
            // read between two style writes is exactly what makes a
            // browser treat each intermediate value as its own transition
            // leg, so instead of one clean resize the line visibly
            // shrinks, overshoots, shrinks again, etc. None of these
            // intermediate values are meant to be seen - only the final,
            // settled size is - so the transition is switched off for the
            // duration of this correction loop and restored right after,
            // on the next frame once the size has already stopped
            // changing (so nothing has anything left to animate through).
            const prevTransition = el.style.transition;
            el.style.transition = 'none';

            let size = guessSize;
            el.style.fontSize = size + 'px';
            for (let i = 0; i < 6; i++) {
                const actualWidth = el.scrollWidth;
                if (actualWidth <= availWidth + 0.5 || size <= minSize) break;
                const ratio = availWidth / actualWidth;
                const next = Math.max(minSize, Math.floor(size * ratio * 0.985));
                if (next >= size) break;
                size = next;
                el.style.fontSize = size + 'px';
            }
            // Extra passes below the normal floor, only entered if it's
            // still overflowing there.
            for (let i = 0; i < 8 && size > HARD_FLOOR_PX; i++) {
                const actualWidth = el.scrollWidth;
                if (actualWidth <= availWidth + 0.5) break;
                const ratio = availWidth / actualWidth;
                const next = Math.max(HARD_FLOOR_PX, Math.floor(size * ratio * 0.985));
                if (next >= size) break;
                size = next;
                el.style.fontSize = size + 'px';
            }

            // Flush the final size so the browser has committed it before
            // transitions come back on, then hand control of `transition`
            // back to the stylesheet (not to a hardcoded value) so any
            // later legitimate change (e.g. this same line swapping from
            // adjacent to active) still gets the designed fade.
            void el.offsetHeight;
            requestAnimationFrame(() => {
                el.style.transition = prevTransition;
            });
            return size;
        }

        // ---------- Coordinated crossfade text swap ----------
        // All three slots are computed together before anything is touched,
        // so prev/active/next never briefly show mismatched sizes.
        const FADE_MS = 90;
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

        // Sets the text and its font-size together, verifying the real
        // rendered width against the DOM (not just the canvas estimate)
        // before the line is ever revealed - all synchronous, so this adds
        // no extra animation frame / delay versus the old estimate-only
        // path.
        function applySizedText(inner, text, isActive) {
            const { size: guessSize, availWidth } = computeFontSize(text, isActive);
            inner.textContent = text;
            if (!text) {
                inner.style.fontSize = guessSize + 'px';
                return;
            }
            const minSize = isActive ? ACTIVE_MIN : ADJACENT_MIN;
            fitTextToWidth(inner, guessSize, minSize, availWidth);
        }

        function setSlot(slot, text) {
            const inner = slot.inner;
            if (inner.dataset.text === text) return;
            const hadContent = !!inner.dataset.text;
            inner.dataset.text = text;

            clearTimeout(inner._fadeTimer);
            if (!hadContent && !inner.textContent) {
                // Nothing was showing yet - fade straight in, no need to
                // fade out first.
                applySizedText(inner, text, slot.isActive);
                requestAnimationFrame(() => {
                    inner.style.opacity = text ? String(slot.opacity) : '0';
                });
                return;
            }

            inner.style.opacity = '0';
            inner._fadeTimer = setTimeout(() => {
                applySizedText(inner, text, slot.isActive);
                requestAnimationFrame(() => {
                    inner.style.opacity = text ? String(slot.opacity) : '0';
                });
            }, FADE_MS);
        }

        function refitCurrentLines() {
            Object.values(slots).forEach(slot => {
                const text = slot.inner.dataset.text || '';
                if (!text) return;
                applySizedText(slot.inner, text, slot.isActive);
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

        // ---------- Now-playing title: fit, and marquee-scroll if it still
        // doesn't fit ----------
        // First the same idea as the lyric auto-fit: shrink to the exact
        // width available, down to a readable floor. If the text is still
        // wider than the pill at that floor size, it switches to a
        // left-aligned auto-scrolling marquee instead of ellipsis-clipping
        // forever, so the whole title eventually becomes visible.
        const titleEl = document.getElementById('now-playing-title');
        const titleInnerEl = document.getElementById('now-playing-title-inner');
        const TITLE_MAX = 15, TITLE_MIN = 9;
        const MARQUEE_PX_PER_SEC = 38;
        // Matches the hold/travel split in the marquee-scroll keyframes
        // below (6%-94% is the travel leg = 88% of one cycle).
        const MARQUEE_TRAVEL_FRACTION = 0.88;
        let currentTitleText = '';

        const TITLE_LETTER_SPACING = 0.2; // px, matches #now-playing-title-inner's letter-spacing

        function measureTitleWidthAtRef(text) {
            measureCtx.font = `700 ${REF_SIZE}px 'Montserrat', sans-serif`;
            // Same fix as the lyric lines: the title also renders
            // uppercase (inherited from body), so it must be measured
            // uppercase too, or the solved size comes out too big and the
            // real line overflows.
            return measureCtx.measureText(text.toUpperCase()).width || 1;
        }

        function computeTitleFontSize(text) {
            const availWidth = Math.max(1, titleEl.clientWidth * 0.97);
            if (!text) return { size: TITLE_MAX, availWidth };
            const refWidth = measureTitleWidthAtRef(text);
            const spacingExtra = text.length * TITLE_LETTER_SPACING;
            const usableWidth = Math.max(1, availWidth - spacingExtra);
            let size = (usableWidth / refWidth) * REF_SIZE;
            size = Math.min(size, TITLE_MAX);
            size = Math.max(size, TITLE_MIN);
            return { size: Math.round(size * 10) / 10, availWidth };
        }

        // Fully synchronous, no requestAnimationFrame round trip: the
        // canvas estimate is applied, then immediately checked and
        // corrected against the real live element (scrollWidth reflects
        // full un-clipped content width even while overflow:hidden hides
        // the excess), all before this function returns. That is what
        // keeps title changes feeling instant rather than adding a frame
        // of visible delay.
        function applyTitleLayout() {
            if (!currentTitleText) return;
            titleInnerEl.classList.remove('marquee');
            titleEl.classList.remove('marquee-active');
            titleInnerEl.style.removeProperty('--marquee-distance');

            const { size: guessSize, availWidth } = computeTitleFontSize(currentTitleText);
            let size = guessSize;
            titleInnerEl.style.fontSize = size + 'px';
            for (let i = 0; i < 6; i++) {
                const actualWidth = titleInnerEl.scrollWidth;
                if (actualWidth <= availWidth + 0.5 || size <= TITLE_MIN) break;
                const ratio = availWidth / actualWidth;
                const next = Math.max(TITLE_MIN, Math.round(size * ratio * 0.985 * 10) / 10);
                if (next >= size) break;
                size = next;
                titleInnerEl.style.fontSize = size + 'px';
            }

            // Even at the readable floor size, some titles (very long
            // "Song (feat. Someone Else) • Artist" strings especially)
            // still don't fit the pill - that's what the marquee is for,
            // and it needs the real overflow amount, not the canvas
            // estimate, to travel exactly as far as the text is long.
            const overflow = titleInnerEl.scrollWidth - titleEl.clientWidth;
            if (overflow > 2) {
                const distance = overflow + 20;
                const travelSeconds = distance / MARQUEE_PX_PER_SEC;
                const duration = Math.max(4, travelSeconds / MARQUEE_TRAVEL_FRACTION);
                titleInnerEl.style.setProperty('--marquee-distance', `-${distance}px`);
                titleInnerEl.style.setProperty('--marquee-duration', `${duration.toFixed(2)}s`);
                titleEl.classList.add('marquee-active');
                titleInnerEl.classList.add('marquee');
            }
        }

        function fitTitle() {
            applyTitleLayout();
        }

        function escapeHtml(s) {
            return String(s)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }

        // Song title and artist are rendered as two distinctly-weighted/
        // -colored spans (title bright & bold, artist dimmer & lighter)
        // joined by a small centered dot, instead of a plain
        // "title — artist" string. Measurement/marquee logic still works
        // off a plain-text equivalent (same length, so width math is
        // unaffected by the markup).
        function setTitle(title, artist) {
            const text = artist ? `${title} • ${artist}` : title;
            if (text === currentTitleText) return;
            currentTitleText = text;
            titleInnerEl.classList.remove('marquee');
            titleEl.classList.remove('marquee-active');
            if (artist) {
                titleInnerEl.innerHTML =
                    `<span class="tt-song">${escapeHtml(title)}</span>` +
                    `<span class="tt-sep">&nbsp;&bull;&nbsp;</span>` +
                    `<span class="tt-artist">${escapeHtml(artist)}</span>`;
            } else {
                titleInnerEl.textContent = title;
            }
            applyTitleLayout();
        }

        // ---------- Progress ring / seek ----------
        // A ring that traces the whole rounded-rect perimeter of the
        // controls pill, built from an SVG path so filling it is just a
        // stroke-dasharray on a path with a known total length. Dragging
        // (or a single click/tap) anywhere along the ring seeks to that
        // point in the track; while a seek round trip is in flight the
        // ring is driven purely from the local drag position.
        const ringSvg = document.getElementById('progress-ring');
        const ringGroup = document.getElementById('progress-ring-group');
        const ringBg = document.getElementById('progress-track-bg');
        const ringFill = document.getElementById('progress-track-fill');
        const ringHit = document.getElementById('progress-hit');
        const ringThumb = document.getElementById('progress-thumb');
        const controlsBarEl = document.getElementById('controls-bar');

        const RING_MARGIN = 6; // inset from the pill's outer edge
        const RING_RADIUS = 34; // corner radius of the traced path
        let ringTotalLength = 0;
        let ringSamples = [];
        let lastRingRatio = -1;

        function buildRingPath(w, h, r) {
            r = Math.max(0, Math.min(r, w / 2, h / 2));
            return `M ${w / 2} 0 L ${w - r} 0 A ${r} ${r} 0 0 1 ${w} ${r} ` +
                   `L ${w} ${h - r} A ${r} ${r} 0 0 1 ${w - r} ${h} ` +
                   `L ${r} ${h} A ${r} ${r} 0 0 1 0 ${h - r} ` +
                   `L 0 ${r} A ${r} ${r} 0 0 1 ${r} 0 Z`;
        }

        function buildRingSamples() {
            ringSamples = [];
            if (!ringTotalLength) return;
            const STEPS = 96;
            for (let i = 0; i <= STEPS; i++) {
                const len = (i / STEPS) * ringTotalLength;
                const pt = ringFill.getPointAtLength(len);
                ringSamples.push({ x: pt.x, y: pt.y, len: len });
            }
        }

        function layoutRing() {
            const w = controlsBarEl.clientWidth;
            const h = controlsBarEl.clientHeight;
            if (!w || !h) return;
            ringSvg.setAttribute('width', w);
            ringSvg.setAttribute('height', h);
            const pw = Math.max(1, w - RING_MARGIN * 2);
            const ph = Math.max(1, h - RING_MARGIN * 2);
            const d = buildRingPath(pw, ph, RING_RADIUS);
            ringBg.setAttribute('d', d);
            ringFill.setAttribute('d', d);
            ringHit.setAttribute('d', d);
            ringGroup.setAttribute('transform', `translate(${RING_MARGIN}, ${RING_MARGIN})`);
            ringTotalLength = ringFill.getTotalLength();
            buildRingSamples();
            lastRingRatio = -1;
            setProgressVisual(isSeeking ? seekPositionMs / (trackDurationMs || 1) : (trackDurationMs ? currentDisplayRatio() : 0));
        }

        function currentDisplayRatio() {
            const progress = isPlaying ? serverProgress + (performance.now() - serverTimestamp) : serverProgress;
            return trackDurationMs > 0 ? progress / trackDurationMs : 0;
        }

        if (window.ResizeObserver) {
            new ResizeObserver(() => layoutRing()).observe(controlsBarEl);
        } else {
            window.addEventListener('resize', layoutRing);
        }

        function setProgressVisual(ratio) {
            ratio = Math.min(1, Math.max(0, ratio || 0));
            // Skip sub-pixel-scale updates - avoids doing path geometry
            // math and DOM writes every single animation frame for a
            // change nobody could see.
            if (Math.abs(ratio - lastRingRatio) < 0.0006) return;
            lastRingRatio = ratio;
            if (!ringTotalLength) return;
            const filledLen = ratio * ringTotalLength;
            ringFill.setAttribute('stroke-dasharray', `${filledLen} ${ringTotalLength}`);
            const pt = ringFill.getPointAtLength(filledLen);
            ringThumb.setAttribute('cx', pt.x);
            ringThumb.setAttribute('cy', pt.y);
        }

        function ratioFromLocalPoint(x, y) {
            if (!ringSamples.length) return 0;
            let bestIdx = 0, bestDist = Infinity;
            for (let i = 0; i < ringSamples.length; i++) {
                const s = ringSamples[i];
                const dx = s.x - x, dy = s.y - y;
                const dist = dx * dx + dy * dy;
                if (dist < bestDist) { bestDist = dist; bestIdx = i; }
            }
            // Refine locally between the neighbouring samples for a
            // smoother, more precise hit point than the coarse grid alone.
            const lastIdx = ringSamples.length - 1;
            const lo = Math.max(0, bestIdx - 1), hi = Math.min(lastIdx, bestIdx + 1);
            let bestLen = ringSamples[bestIdx].len;
            const REFINE = 16;
            for (let i = 0; i <= REFINE; i++) {
                const len = ringSamples[lo].len + (ringSamples[hi].len - ringSamples[lo].len) * (i / REFINE);
                const pt = ringFill.getPointAtLength(len);
                const dx = pt.x - x, dy = pt.y - y;
                const dist = dx * dx + dy * dy;
                if (dist < bestDist) { bestDist = dist; bestLen = len; }
            }
            return ringTotalLength > 0 ? bestLen / ringTotalLength : 0;
        }

        function ringLocalPointFromEvent(e) {
            const rect = ringSvg.getBoundingClientRect();
            const clientX = e.touches && e.touches.length ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches && e.touches.length ? e.touches[0].clientY : e.clientY;
            return { x: clientX - rect.left - RING_MARGIN, y: clientY - rect.top - RING_MARGIN };
        }

        function updateSeekFromEvent(e) {
            if (!trackDurationMs) return;
            const p = ringLocalPointFromEvent(e);
            const ratio = ratioFromLocalPoint(p.x, p.y);
            setProgressVisual(ratio);
            seekPositionMs = Math.round(ratio * trackDurationMs);
        }

        function startSeek(e) {
            if (!trackDurationMs) return;
            isSeeking = true;
            ringSvg.classList.add('seeking');
            if (e.pointerId != null && ringHit.setPointerCapture) {
                try { ringHit.setPointerCapture(e.pointerId); } catch (err) {}
            }
            updateSeekFromEvent(e);
            e.preventDefault();
        }

        function endSeek() {
            if (!isSeeking) return;
            isSeeking = false;
            ringSvg.classList.remove('seeking');
            serverProgress = seekPositionMs;
            serverTimestamp = performance.now();
            // Spotify's own state takes a moment to settle after a seek
            // PUT - a poll response landing in that window can carry the
            // pre-seek position and yank the ring backward before the
            // catch-up poll corrects it again (the "glitches forward then
            // back" symptom). Holding our own optimistic position as the
            // source of truth for a short grace window, instead of letting
            // the very next poll response overwrite it, is what keeps the
            // ring moving in one smooth direction through a seek.
            seekGraceUntil = performance.now() + 1500;
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
            // Give Spotify's own backend a beat to actually settle into
            // the new position before we read it back - polling for it
            // immediately is exactly what raced a stale snapshot against
            // the seek in the old flow. The regular 700ms poll loop still
            // picks it up right after this, well within the grace window.
            setTimeout(() => pollServer(true), 450);
        }

        if (window.PointerEvent) {
            ringHit.addEventListener('pointerdown', startSeek);
            ringHit.addEventListener('pointermove', (e) => { if (isSeeking) updateSeekFromEvent(e); });
            ringHit.addEventListener('pointerup', endSeek);
            ringHit.addEventListener('pointercancel', endSeek);
        } else {
            ringHit.addEventListener('mousedown', startSeek);
            ringHit.addEventListener('touchstart', startSeek, { passive: false });
            window.addEventListener('mousemove', (e) => { if (isSeeking) updateSeekFromEvent(e); });
            window.addEventListener('touchmove', (e) => { if (isSeeking) { updateSeekFromEvent(e); e.preventDefault(); } }, { passive: false });
            window.addEventListener('mouseup', endSeek);
            window.addEventListener('touchend', endSeek);
        }
        window.addEventListener('touchcancel', endSeek);

        // ---------- Polling (guarded against overlap / out-of-order) ----------
        let pollInFlight = false;
        let pollSeq = 0;
        let missCount = 0;
        let transientCount = 0;

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
                if (data.trackId) transientCount = 0;

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

                if (data.trackId) {
                    // Whether it's actually playing or just paused-but-
                    // loaded, a track being present is what matters for
                    // initializing the screen: background color, lyrics
                    // and title all need to reflect it either way. This
                    // runs the same regardless of play state so that
                    // connecting (or refreshing) while a song is paused
                    // shows that song immediately instead of waiting for
                    // playback to start.
                    isPlaying = !!effectiveIsPlaying;
                    if (!isSeeking && performance.now() > seekGraceUntil) {
                        serverProgress = data.progressMs;
                        serverTimestamp = performance.now() - networkLatency;
                    }
                    trackDurationMs = data.durationMs || 0;
                    updatePlayPauseIcon();
                    setTitle(data.title, data.artist);

                    if (cachedTrackId !== data.trackId) {
                        cachedTrackId = data.trackId;
                        parsedLines = data.lines || [];
                        // Land straight on whatever line is current for
                        // this track's actual progress, instead of -2
                        // (which would blank the screen and wait for the
                        // next progress tick to pick the right line -
                        // exactly the "nothing shows until playback
                        // starts" symptom).
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

                        // If we're not actually playing yet (e.g. the
                        // track was paused when we connected), still show
                        // the lyric line that matches the current saved
                        // position right away rather than waiting for the
                        // animation loop's isPlaying-gated update.
                        if (!isPlaying && parsedLines.length > 0) {
                            let activeIndex = -1;
                            for (let i = 0; i < parsedLines.length; i++) {
                                if (parsedLines[i].startTimeMs <= data.progressMs) activeIndex = i;
                                else break;
                            }
                            lastActiveIndex = activeIndex;
                            const prevText = activeIndex > 0 ? parsedLines[activeIndex - 1].words : "";
                            const activeText = activeIndex >= 0 ? parsedLines[activeIndex].words : "";
                            const nextText = activeIndex + 1 < parsedLines.length ? parsedLines[activeIndex + 1].words : "";
                            applyLines(prevText, activeText, nextText);
                        }
                    }
                } else if (data.transient) {
                    // The server hit a hiccup (network blip, token refresh,
                    // a rejected/expired token, a bad Spotify response) - it
                    // is explicitly NOT telling us playback stopped. Leave
                    // everything exactly as it is (last track, lyrics,
                    // progress keep advancing off the last known-good
                    // anchor) and just retry sooner than the normal cadence
                    // so a real recovery shows up fast. This is what keeps
                    // the screen locked to the last playing song instead of
                    // going black on a transient error.
                    transientCount++;
                    // Fast-retry the first several misses to recover almost
                    // instantly from a blip; beyond that, fall back to the
                    // normal poll cadence instead of hammering the network
                    // if something stays down for a while.
                    if (transientCount <= 15) setTimeout(() => pollServer(true), 200);
                } else {
                    // Spotify itself confirmed there's no active session
                    // anywhere (Spotify isn't open / nothing loaded). This
                    // is the one legitimate reason to blank the screen.
                    transientCount = 0;
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
                // Network hiccup talking to our own backend: same
                // treatment as a transient server response - keep showing
                // the last known state and retry quickly instead of
                // silently sitting stuck or blanking out.
                missCount++;
                if (missCount <= 15) setTimeout(() => pollServer(true), 200);
            } finally {
                clearTimeout(timeoutId);
                if (mySeq === pollSeq) pollInFlight = false;
            }
        }

        layoutRing();
        setInterval(() => pollServer(false), 700);
        pollServer(true);

        let ringFrameCount = 0;
        function animationLoop() {
            const currentProgress = isPlaying
                ? serverProgress + (performance.now() - serverTimestamp)
                : serverProgress;

            // Drive the progress ring smoothly, except while the user is
            // actively dragging it (their own drag position is the source
            // of truth then). Path geometry math (getPointAtLength) is
            // real work, so it only runs a few times a second - at that
            // rate the sweep still looks perfectly continuous but costs a
            // fraction of doing it every single animation frame, which
            // matters on the underpowered head units this runs on.
            ringFrameCount++;
            if (!isSeeking && trackDurationMs > 0 && ringFrameCount % 3 === 0) {
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

def get_valid_token(force=False):
    if not force and time.time() < session.get('expires_at', 0):
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
    """Word-wrap a single lyric line into chunks that each fit comfortably
    on one display line.

    A naive greedy fill (pack words onto the current chunk until the next
    one wouldn't fit, then start a new chunk) tends to dump whatever is
    left over into a final chunk by itself - often just one short word -
    once the preceding chunks have already eaten most of max_chars. That
    lone-word chunk then gets its own timed sub-line on screen, which reads
    as a jarring "just one word" flash. This still greedy-fills first (that
    part was never the problem), but then rebalances afterwards: any chunk
    that ended up as a single word gets folded into whichever neighbouring
    chunk it fits best against, even if that neighbour then runs a bit past
    max_chars - the client always shrinks font size to fit whatever text
    actually lands on a line, so a soft, occasional overrun here is far
    less noticeable than a whole display line holding one word."""
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
    if not chunks:
        return [text]

    OVERRUN_TOLERANCE = 1.4  # how far past max_chars a merge may push a chunk
    changed = True
    while changed and len(chunks) > 1:
        changed = False
        for i, chunk in enumerate(chunks):
            if len(chunk.split()) != 1:
                continue
            candidates = []
            if i > 0:
                candidates.append((i - 1, len(chunks[i - 1]) + 1 + len(chunk)))
            if i + 1 < len(chunks):
                candidates.append((i + 1, len(chunk) + 1 + len(chunks[i + 1])))
            if not candidates:
                continue
            target_i, merged_len = min(candidates, key=lambda c: c[1])
            if merged_len > max_chars * OVERRUN_TOLERANCE:
                continue
            if target_i < i:
                chunks[target_i] = chunks[target_i] + " " + chunk
            else:
                chunks[target_i] = chunk + " " + chunks[target_i]
            del chunks[i]
            changed = True
            break

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

# Lyrics for a given track never change, but /api/now-playing is polled
# every 700ms and also re-hit immediately after every control tap (play,
# pause, seek, next, previous) so the UI can refresh right away. Without a
# cache, every single one of those calls was doing a live network round
# trip to LRCLIB - which is what actually caused the "lag when pausing /
# using controls" (not client-side rendering). The cache only lets LRCLIB
# get hit once per track, keyed by Spotify's track id.
LYRICS_CACHE = {}
LYRICS_CACHE_MAX = 100

def get_cached_lyrics(track_id, track_name, artist_name):
    if track_id and track_id in LYRICS_CACHE:
        return LYRICS_CACHE[track_id]

    lines = fetch_synced_lyrics(track_name, artist_name)

    if track_id:
        if len(LYRICS_CACHE) >= LYRICS_CACHE_MAX:
            LYRICS_CACHE.pop(next(iter(LYRICS_CACHE)))
        LYRICS_CACHE[track_id] = lines

    return lines

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
    # "transient": True on any of these responses tells the client this
    # is a hiccup (network blip, expired/rejected token, Spotify rate
    # limit, a bad response body) rather than Spotify genuinely reporting
    # nothing is playing. The client keeps showing whatever it already
    # had on a transient response instead of blanking the screen - it
    # only blanks when Spotify itself confirms there's no active session
    # (a real 204, or a 200 with an empty player object), which is the
    # "Spotify isn't open" case. That split is what keeps the display
    # locked to the last playing song through momentary poll failures
    # instead of going black and getting stuck there.
    token = get_valid_token()
    if not token:
        return jsonify({"isPlaying": False, "trackId": None, "transient": True})

    # /v1/me/player (rather than /v1/me/player/currently-playing) is used
    # here because it reports the full playback state tied to the active
    # device - including a track that's loaded but paused - as long as a
    # device session exists at all. That's what lets the very first poll
    # right after connecting show whatever track was already loaded
    # (playing or paused) instead of staying blank until a new song starts.
    def fetch_player(tok):
        return requests.get(
            "https://api.spotify.com/v1/me/player",
            headers={"Authorization": f"Bearer {tok}"},
            timeout=4
        )

    try:
        player_res = fetch_player(token)
        # A 401 here means the access token we had was rejected even
        # though we thought it was still valid (clock skew, a token
        # revoked early, etc). One forced refresh-and-retry recovers
        # from that immediately instead of surfacing a blank screen and
        # waiting for the next poll to happen to fix itself.
        if player_res.status_code == 401:
            fresh_token = get_valid_token(force=True)
            if fresh_token:
                player_res = fetch_player(fresh_token)
    except Exception:
        return jsonify({"isPlaying": False, "trackId": None, "transient": True})

    if player_res.status_code == 204:
        # No active Spotify Connect session at all - Spotify itself isn't
        # open/playing anywhere. This is the one genuine "nothing to show".
        return jsonify({"isPlaying": False, "trackId": None})

    if not player_res.ok:
        # 401/403/429/5xx - Spotify or our own request failed, not the
        # same thing as "nothing is playing". Don't blank on this.
        return jsonify({"isPlaying": False, "trackId": None, "transient": True})

    try:
        player = player_res.json()
    except Exception:
        return jsonify({"isPlaying": False, "trackId": None, "transient": True})

    if not player:
        # A 200 with a genuinely empty body is Spotify's other way of
        # saying no active device/session - treat it the same as 204.
        return jsonify({"isPlaying": False, "trackId": None})

    item = player.get('item') or {}
    track_id = item.get('id') or ""
    track_name = item.get('name') or ""
    artists = item.get('artists') or []
    artist_name = artists[0].get('name', '') if artists and isinstance(artists[0], dict) else ""

    if not track_name or not artist_name:
        # The player object came back but without a usable track - an odd
        # transient shape (e.g. mid-transition between tracks), not proof
        # playback stopped. Keep whatever the client already has.
        return jsonify({"isPlaying": False, "trackId": None, "transient": True})

    album = item.get('album') or {}
    images = album.get('images') or []
    album_art = images[0].get('url', '') if images and isinstance(images[0], dict) else ""

    lines = get_cached_lyrics(track_id, track_name, artist_name)
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