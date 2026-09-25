import os
import time
import requests
import urllib.parse
import base64
import re
import threading
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

        /* --roll-ms is written by the script from its TIMING table, so
           the CSS crossfade and the JS swap logic share one definition.
           The value here is only a fallback for the first paint. */
        :root {
            --roll-ms: 320ms;
            --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
            --ease-std: cubic-bezier(0.4, 0, 0.2, 1);
            --lyrics-h: calc(100dvh - 96px);
            /* Slot heights - written per track by the script (see
               layoutSlots) from the song's own line sizes. */
            --active-h: min(115px, calc(var(--lyrics-h) * 0.26));
            --adj-h: min(46px, calc(var(--lyrics-h) * 0.13));
        }

        @keyframes rise-in {
            from { opacity: 0; transform: translate3d(0, 14px, 0) scale(0.985); }
            to   { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
        }
        @keyframes breathe {
            0%, 100% { opacity: 0.55; }
            50%      { opacity: 1; }
        }

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
            transition: background-color 1.4s var(--ease-std),
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
        .fonts-ready .login-container {
            animation: rise-in 520ms var(--ease-out) both;
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
        .pill-input:hover { border-color: rgba(29, 185, 84, 0.6); }
        input.pill-input:focus {
            border-color: #1DB954;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4), 0 0 0 3px rgba(29, 185, 84, 0.18);
            background: rgba(24, 24, 24, 0.9);
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
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 25px rgba(29, 185, 84, 0.4);
        }
        @media (hover: hover) {
            .pill-button:hover {
                background: #21cf5e;
                transform: translateY(-1px);
                box-shadow: 0 12px 30px rgba(29, 185, 84, 0.5);
            }
        }
        .pill-button:active {
            transform: scale(0.97);
            transition-duration: 80ms;
            box-shadow: 0 4px 14px rgba(29, 185, 84, 0.35);
        }

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
            height: var(--lyrics-h);
            position: relative;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 1.2vh;
            z-index: 10;
            box-sizing: border-box;
        }

        /* Every slot has a FIXED height for the duration of a track, so
           the three lines never move when a neighbour is empty (first/
           last line of a song) or when one line is shorter than the
           last. The height is fitted to THIS song's lines (the median
           line's natural size) so the stack stays tight; the few lines
           that would be bigger are capped to the slot instead. A new
           track morphs the heights rather than snapping them. */
        .lyric-line {
            width: 100%;
            position: relative;
            flex: 0 0 auto;
            transition: height var(--roll-ms) var(--ease-out);
        }
        .adjacent-line { height: var(--adj-h); }
        .active-line   { height: var(--active-h); }

        /* Two stacked layers per slot. A line change is a true
           crossfade: the incoming layer fades/slides in while the
           outgoing one fades/slides out AT THE SAME TIME, so the screen
           never dips to black between lines (the old fade-out-then-
           fade-in read as a flicker). Direction follows playback
           (forward = new line rises in from below, old line exits
           upward), reversed when going backwards. */
        .lyric-layer {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transform: translate3d(0, 0, 0);
            transition: opacity var(--roll-ms) var(--ease-out), transform var(--roll-ms) var(--ease-out);
            will-change: opacity, transform;
            pointer-events: none;
            backface-visibility: hidden;
        }

        .lyric-inner {
            white-space: nowrap;
            padding: 0 10px;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
            line-height: 1.15;
        }

        .adjacent-line .lyric-inner {
            font-weight: 600;
        }

        .active-line .lyric-inner {
            font-weight: 900;
            text-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        /* "Nothing playing" / "No synced lyrics": small, quiet, and
           breathing slowly so the screen reads as alive, not stuck. */
        .lyric-layer.is-placeholder .lyric-inner {
            font-weight: 600;
            text-shadow: none;
            letter-spacing: 3px;
            color: rgba(255, 255, 255, 0.85);
            animation: breathe 3.2s ease-in-out infinite;
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
        .fonts-ready #controls-bar {
            animation: rise-in 620ms var(--ease-out) both;
            animation-delay: 60ms;
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
            r: 5.5;
            transition: opacity 0.18s var(--ease-std), fill 0.15s ease, r 0.2s var(--ease-out);
        }
        #progress-ring.seeking #progress-thumb { r: 7; }

        /* Spotify rejected the seek (no active device, restricted
           device, rate limit): brief red flash on the thumb. */
        #progress-thumb.seek-failed {
            opacity: 1;
            fill: #ff5252;
        }

        #controls-bar:hover #progress-thumb,
        #progress-ring.seeking #progress-thumb {
            opacity: 1;
        }

        /* The fill is driven every animation frame from JS; a CSS
           transition stacked on top of that only lagged and stair-stepped
           the sweep, so there is none. */
        #progress-track-fill {
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
            transition: opacity 180ms var(--ease-std), transform 180ms var(--ease-out);
        }
        #now-playing-title.swapping {
            opacity: 0;
            transform: translate3d(0, 4px, 0);
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
            border-radius: 50%;
            outline: none;
            touch-action: manipulation;
            transition: transform 220ms var(--ease-out), opacity 180ms var(--ease-std), background-color 180ms var(--ease-std);
            opacity: 0.72;
            will-change: transform;
        }

        /* Hover only where a hover actually exists - on a touch head
           unit :hover sticks after a tap and left one button "lit". */
        @media (hover: hover) {
            .control-btn:hover {
                opacity: 1;
                transform: scale(1.08);
                background-color: rgba(255, 255, 255, 0.06);
            }
        }
        .control-btn.pressed {
            opacity: 1;
            transform: scale(0.84);
            background-color: rgba(255, 255, 255, 0.1);
            transition-duration: 70ms;
        }

        .control-btn svg {
            fill: white;
            width: 24px;
            height: 24px;
            display: block;
        }

        /* Play <-> pause morph: both glyphs are always in the SVG and
           swap with a scale/rotate crossfade instead of an innerHTML
           replace that popped from one to the other. */
        #play-pause-icon path {
            transform-box: fill-box;
            transform-origin: center;
            transition: opacity 180ms var(--ease-std), transform 260ms var(--ease-out);
        }
        #play-pause-icon .ic-play  { opacity: 0; transform: scale(0.55) rotate(-90deg); }
        #play-pause-icon .ic-pause { opacity: 1; transform: scale(1) rotate(0deg); }
        #play-pause-icon.is-paused .ic-play  { opacity: 1; transform: scale(1) rotate(0deg); }
        #play-pause-icon.is-paused .ic-pause { opacity: 0; transform: scale(0.55) rotate(90deg); }

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
        <div class="lyric-line adjacent-line" id="prev-line">
            <div class="lyric-layer is-current"><span class="lyric-inner"></span></div>
            <div class="lyric-layer"><span class="lyric-inner"></span></div>
        </div>
        <div class="lyric-line active-line" id="active-line">
            <div class="lyric-layer is-current"><span class="lyric-inner"></span></div>
            <div class="lyric-layer"><span class="lyric-inner"></span></div>
        </div>
        <div class="lyric-line adjacent-line" id="next-line">
            <div class="lyric-layer is-current"><span class="lyric-inner"></span></div>
            <div class="lyric-layer"><span class="lyric-inner"></span></div>
        </div>
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
                <svg viewBox="0 0 24 24" id="play-pause-icon" class="is-paused">
                    <path class="ic-pause" d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                    <path class="ic-play" d="M8 5v14l11-7z"/>
                </svg>
            </button>
            <button class="control-btn" onclick="sendControl('next')">
                <svg viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
            </button>
        </div>
    </div>

    <script>
        const colorThief = new ColorThief();
        const NOSLEEP_SRC = "data:video/mp4;base64,{{ nosleep_video }}";

        // =====================================================================
        // TIMING - the single place every duration in this page is defined.
        // The CSS crossfade duration is written *from* here (see the
        // --roll-ms custom property below) so JS and CSS can never drift.
        // =====================================================================
        const TIMING = {
            ROLL_MS: 320,              // lyric crossfade (both layers move at once)
            LYRIC_LEAD_MS: 130,        // start the roll this early so the incoming line is
                                       // fully readable exactly when the word is sung
            TITLE_SWAP_MS: 150,        // title fade-out before the new title is written
            POLL_MS: 400,              // steady-state poll cadence
            RETRY_MS: 250,             // fast retry after a transient / ignored response
            RETRY_MAX: 20,             // fast retries in a row before falling back to POLL_MS
            FETCH_TIMEOUT_MS: 6000,    // abort a /api/now-playing request after this
            PLAYPAUSE_HOLD_MS: 4000,   // trust optimistic play/pause until confirmed or this passes
            SEEK_HOLD_MS: 6000,        // trust optimistic seek position until confirmed or this passes
            SEEK_TOLERANCE_MS: 2500,   // server progress within this of ours = seek confirmed
            SKIP_HOLD_MS: 4000,        // wait for the track id to change after next/previous
            CONTROL_GRACE_MS: 8000,    // no blanking within this long after any local action
            EMPTY_CONFIRM_COUNT: 5,    // consecutive genuine "nothing playing" polls before blanking...
            EMPTY_CONFIRM_MS: 4000,    // ...and they must span at least this long
            DRIFT_SNAP_MS: 1500,       // progress error above this snaps; below it is eased out
            DRIFT_EASE: 0.35,          // fraction of the remaining error removed per poll
            SEEK_FAIL_FLASH_MS: 600,   // thumb flashes red this long when Spotify rejects a seek
            RESIZE_DEBOUNCE_MS: 120,
            RESIZE_RECHECK_MS: 400
        };
        document.documentElement.style.setProperty('--roll-ms', TIMING.ROLL_MS + 'ms');

        // ---------- Opacity targets per slot ----------
        const OPACITY_ACTIVE = 1;
        const OPACITY_ADJACENT = 0.35;

        // =====================================================================
        // Playback state - ONE source of truth for "where are we in the song".
        //
        // anchorProgressMs is the track position at anchorTime (a
        // performance.now() stamp). currentProgressMs() extrapolates from
        // that while playing and returns it unchanged while paused, and
        // returns the live drag position while the user is seeking. The
        // ring, the lyric line selection, the optimistic controls and the
        // poll reconciliation all read from this one function, so they can
        // never disagree with each other.
        // =====================================================================
        let anchorProgressMs = 0;
        let anchorTime = 0;
        let isPlaying = false;
        let trackDurationMs = 0;
        let cachedTrackId = "";
        let parsedLines = [];
        let lyricsPending = false;
        let lastActiveIndex = -2;

        let isSeeking = false;
        let seekPositionMs = 0;

        let wakeLock = null;
        let noSleepVideo = null;

        function nowMs() { return performance.now(); }

        function setAnchor(progressMs) {
            anchorProgressMs = Math.max(0, progressMs || 0);
            anchorTime = nowMs();
        }

        function currentProgressMs() {
            if (isSeeking) return seekPositionMs;
            let p = isPlaying ? anchorProgressMs + (nowMs() - anchorTime) : anchorProgressMs;
            if (trackDurationMs > 0 && p > trackDurationMs) p = trackDurationMs;
            return p < 0 ? 0 : p;
        }

        // Raw last server snapshot (always recorded, even when the poller
        // decides not to *apply* it). Used to revert a failed optimistic
        // action to exactly what Spotify last said.
        const serverSnap = { trackId: "", progressMs: 0, isPlaying: false, at: 0, valid: false };

        // =====================================================================
        // Local authority - the optimistic-UI mechanism, applied uniformly
        // to play/pause, seek and next/previous.
        //
        // After a local action we know what the state *will* be before
        // Spotify does. Until Spotify's own reports agree with us (or the
        // hold window runs out), poll responses are not allowed to
        // overwrite isPlaying / progress. That is what stops: the icon
        // flickering back after a tap, the ring being yanked to the
        // pre-seek position by a stale snapshot, and a paused ring drifting.
        // =====================================================================
        const localAuth = {
            active: false,
            kind: null,          // 'playpause' | 'seek' | 'skip'
            isPlaying: null,     // expected play state (null = don't care)
            progressMs: null,    // expected position at progressAt (null = don't care)
            progressAt: 0,
            skipFromTrackId: "", // 'skip': the track we expect to leave
            expiresAt: 0
        };
        let lastActionAt = -1e9;

        function assertLocal(kind, opts) {
            localAuth.active = true;
            localAuth.kind = kind;
            localAuth.isPlaying = opts.isPlaying === undefined ? null : opts.isPlaying;
            localAuth.progressMs = opts.progressMs === undefined ? null : opts.progressMs;
            localAuth.progressAt = nowMs();
            localAuth.skipFromTrackId = opts.skipFromTrackId || "";
            localAuth.expiresAt = nowMs() + opts.holdMs;
            lastActionAt = nowMs();
        }

        function releaseLocal() {
            localAuth.active = false;
            localAuth.kind = null;
            localAuth.isPlaying = null;
            localAuth.progressMs = null;
            localAuth.skipFromTrackId = "";
        }

        // Where the local authority expects the track to be right now.
        function localExpectedProgress() {
            if (localAuth.progressMs === null) return null;
            const playing = localAuth.isPlaying === null ? isPlaying : localAuth.isPlaying;
            return localAuth.progressMs + (playing ? nowMs() - localAuth.progressAt : 0);
        }

        // Decide whether a server snapshot agrees with the local authority.
        // Returns 'none' (no authority), 'confirmed', 'expired' or 'hold'.
        function reconcileLocal(data) {
            if (!localAuth.active) return 'none';
            const t = nowMs();
            if (t > localAuth.expiresAt) { releaseLocal(); return 'expired'; }

            if (localAuth.kind === 'skip') {
                if (data.trackId && data.trackId !== localAuth.skipFromTrackId) { releaseLocal(); return 'confirmed'; }
                return 'hold';
            }

            const playingOk = localAuth.isPlaying === null || data.isPlaying === localAuth.isPlaying;
            let progressOk = true;
            const expected = localExpectedProgress();
            if (expected !== null) {
                progressOk = Math.abs((data.progressMs || 0) - expected) <= TIMING.SEEK_TOLERANCE_MS;
            }
            if (playingOk && progressOk) { releaseLocal(); return 'confirmed'; }
            return 'hold';
        }

        // Revert the display to the last thing Spotify actually told us -
        // used when Spotify rejects an optimistic action outright.
        function revertToServerSnapshot() {
            releaseLocal();
            if (!serverSnap.valid || serverSnap.trackId !== cachedTrackId) return;
            isPlaying = serverSnap.isPlaying;
            const p = serverSnap.progressMs + (serverSnap.isPlaying ? nowMs() - serverSnap.at : 0);
            setAnchor(p);
            updatePlayPauseIcon();
            lastActiveIndex = -2;
        }

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

        // =====================================================================
        // Playback controls (all optimistic, all verified against the
        // server's success flag, all reverted on a hard failure)
        // =====================================================================
        let controlSeq = 0;

        async function postControl(body) {
            const res = await fetch('/api/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json().catch(() => ({}));
            return !!data.success;
        }

        function togglePlayPause() {
            requestWakeLock();
            // Anchor at the exact position currently on screen, so pausing
            // freezes the ring where it *is* (not where the last poll said
            // it was, up to a poll interval ago) and resuming continues from
            // the same spot with no forward jump.
            const here = currentProgressMs();
            const target = !isPlaying;
            setAnchor(here);
            isPlaying = target;
            updatePlayPauseIcon();
            assertLocal('playpause', { isPlaying: target, progressMs: here, holdMs: TIMING.PLAYPAUSE_HOLD_MS });

            const mySeq = ++controlSeq;
            postControl({ action: target ? 'play' : 'pause' })
                .then(ok => { if (!ok && mySeq === controlSeq) revertToServerSnapshot(); })
                .catch(() => { if (mySeq === controlSeq) revertToServerSnapshot(); })
                .finally(() => pollServer(true));
        }

        function sendControl(action) {
            requestWakeLock();
            if (action !== 'next' && action !== 'previous') return;
            // Optimistic skip: the ring drops to zero and the lyrics fade
            // out right away; the title stays until the new track's data
            // lands (so nothing looks "gone"). Poll responses that still
            // carry the old track id are held back until the id changes
            // or the hold window passes (skip refused / end of queue), at
            // which point whatever Spotify reports is accepted again.
            const from = cachedTrackId;
            parsedLines = [];
            lyricsPending = false;
            lastActiveIndex = -2;
            applyLines('', '', '', action === 'next' ? 1 : -1);
            setAnchor(0);
            cachedTrackId = "";
            assertLocal('skip', { skipFromTrackId: from, holdMs: TIMING.SKIP_HOLD_MS });

            const mySeq = ++controlSeq;
            postControl({ action: action })
                .then(ok => { if (!ok && mySeq === controlSeq) { releaseLocal(); } })
                .catch(() => { if (mySeq === controlSeq) releaseLocal(); })
                .finally(() => pollServer(true));
        }

        function updatePlayPauseIcon() {
            // Both glyphs live in the SVG; CSS morphs between them.
            document.getElementById('play-pause-icon').classList.toggle('is-paused', !isPlaying);
        }

        // Press feedback on every control - the button visibly sinks the
        // instant it is touched (before the request is even sent), and
        // springs back on release. :active alone is unreliable on touch
        // head units, so this is driven by pointer events.
        document.querySelectorAll('.control-btn').forEach(btn => {
            const down = () => btn.classList.add('pressed');
            const up = () => btn.classList.remove('pressed');
            btn.addEventListener('pointerdown', down);
            btn.addEventListener('pointerup', up);
            btn.addEventListener('pointercancel', up);
            btn.addEventListener('pointerleave', up);
        });

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
        const LYRIC_LETTER_SPACING = 1.5; // px, matches body's letter-spacing
        const LYRIC_HPAD = 10;            // px, matches .lyric-inner's own padding
        const LYRIC_SAFETY = 8;           // px, extra margin against rounding
        const LINE_HEIGHT = 1.15;         // matches .lyric-inner's line-height

        const measureCanvas = document.createElement('canvas');
        const measureCtx = measureCanvas.getContext('2d');
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => { refitCurrentLines(); fitTitle(); layoutRing(); });
        }

        function measureWidthAtRef(text, weight) {
            measureCtx.font = `${weight} ${REF_SIZE}px 'Montserrat', sans-serif`;
            // The element renders uppercase (inherited from body) so it
            // must be measured uppercase too.
            return measureCtx.measureText(text.toUpperCase()).width || 1;
        }

        // sizeCap (optional): the slot's current maximum font size.
        function computeFontSize(text, isActive, sizeCap) {
            const maxSize = Math.min(isActive ? ACTIVE_MAX : ADJACENT_MAX, sizeCap || Infinity);
            const minSize = isActive ? ACTIVE_MIN : ADJACENT_MIN;
            const spacingExtra = (text || '').length * LYRIC_LETTER_SPACING;
            const rawMaxWidth = containerEl.clientWidth * 0.92 - LYRIC_HPAD * 2 - spacingExtra - LYRIC_SAFETY;
            const availWidth = Math.max(1, rawMaxWidth);
            if (!text) return { size: maxSize, availWidth };

            const weight = isActive ? ACTIVE_WEIGHT : ADJACENT_WEIGHT;
            const refWidth = measureWidthAtRef(text, weight);

            let size = (availWidth / refWidth) * REF_SIZE;

            const maxHeight = containerEl.clientHeight * (isActive ? 0.26 : 0.13);
            size = Math.min(size, maxHeight / LINE_HEIGHT);

            size = Math.min(size, maxSize);
            size = Math.max(size, minSize);
            return { size: Math.round(size), availWidth };
        }

        // Canvas pre-measurement is close but not pixel-exact; verify the
        // real rendered width and nudge down until it fits. This is only
        // ever called while the element is invisible (opacity 0) and with
        // font-size deliberately NOT part of the CSS transition list, so
        // the intermediate sizes written here are never painted and never
        // animate - no layout thrash, no size wobble.
        const HARD_FLOOR_PX = 7;
        function fitTextToWidth(el, guessSize, minSize, availWidth) {
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
            for (let i = 0; i < 8 && size > HARD_FLOOR_PX; i++) {
                const actualWidth = el.scrollWidth;
                if (actualWidth <= availWidth + 0.5) break;
                const ratio = availWidth / actualWidth;
                const next = Math.max(HARD_FLOOR_PX, Math.floor(size * ratio * 0.985));
                if (next >= size) break;
                size = next;
                el.style.fontSize = size + 'px';
            }
            return size;
        }

        // =====================================================================
        // Two-layer crossfade
        //
        // Every slot has two stacked layers. A line change writes the new
        // text (already sized) into the HIDDEN layer, then on the next
        // frame fades/slides that layer in while the visible one fades/
        // slides out - simultaneously. The screen never dips to empty
        // between lines, and because slot heights are fixed nothing else
        // on screen moves. Direction follows playback: forward, the new
        // line rises in from below and the old one exits upward; backward
        // (seek/previous) it is mirrored. A change that arrives mid-roll
        // simply re-targets both layers from wherever they are.
        // =====================================================================
        function makeSlot(id, opacity, isActive, travel) {
            const el = document.getElementById(id);
            const layers = Array.from(el.querySelectorAll('.lyric-layer'));
            return { el, layers, current: 0, opacity, isActive, travel, text: null, placeholder: false, raf: null, sizeCap: 0 };
        }
        const slots = {
            'prev-line': makeSlot('prev-line', OPACITY_ADJACENT, false, 8),
            'active-line': makeSlot('active-line', OPACITY_ACTIVE, true, 14),
            'next-line': makeSlot('next-line', OPACITY_ADJACENT, false, 8)
        };
        let rollDirection = 1;

        function currentLayer(slot) { return slot.layers[slot.current]; }

        // Fit the slot heights to the current song. The natural size of
        // every line is computed once (cheap canvas measurement); the
        // median becomes the slot's font cap, so the stack is as tight as
        // this song's typical line and every line renders at (nearly) the
        // same size - the handful of very short lines that would have
        // ballooned are held to the cap instead.
        function layoutSlots() {
            const activeSizes = [], adjSizes = [];
            for (const line of parsedLines) {
                if (!line.words) continue;
                activeSizes.push(computeFontSize(line.words, true).size);
                adjSizes.push(computeFontSize(line.words, false).size);
            }
            const median = (arr, fallback) => {
                if (!arr.length) return fallback;
                arr.sort((a, b) => a - b);
                return arr[Math.floor(arr.length * 0.5)];
            };
            const activeCap = median(activeSizes, computeFontSize('', true).size);
            const adjCap = median(adjSizes, computeFontSize('', false).size);
            slots['active-line'].sizeCap = activeCap;
            slots['prev-line'].sizeCap = adjCap;
            slots['next-line'].sizeCap = adjCap;
            containerEl.style.setProperty('--active-h', Math.ceil(activeCap * LINE_HEIGHT) + 'px');
            containerEl.style.setProperty('--adj-h', Math.ceil(adjCap * LINE_HEIGHT) + 'px');
        }

        // direction: +1 forward (default), -1 backward
        function applyLines(prevText, activeText, nextText, direction) {
            if (direction) rollDirection = direction < 0 ? -1 : 1;
            setSlot(slots['prev-line'], prevText || '');
            setSlot(slots['active-line'], activeText || '');
            setSlot(slots['next-line'], nextText || '');
        }

        // Quiet status line in the active slot ("Nothing playing", "No
        // synced lyrics") - so the screen is never just black.
        function showPlaceholder(text) {
            setSlot(slots['prev-line'], '');
            setSlot(slots['active-line'], text, true);
            setSlot(slots['next-line'], '');
        }

        const PLACEHOLDER_SIZE = 13;
        function applySizedText(inner, text, isActive, placeholder, sizeCap) {
            inner.textContent = text;
            if (placeholder) {
                inner.style.fontSize = PLACEHOLDER_SIZE + 'px';
                return;
            }
            const { size: guessSize, availWidth } = computeFontSize(text, isActive, sizeCap);
            if (!text) {
                inner.style.fontSize = guessSize + 'px';
                return;
            }
            const minSize = isActive ? ACTIVE_MIN : ADJACENT_MIN;
            fitTextToWidth(inner, guessSize, minSize, availWidth);
        }

        function setSlot(slot, text, placeholder) {
            placeholder = !!placeholder;
            if (slot.text === text && slot.placeholder === placeholder) return;
            slot.text = text;
            slot.placeholder = placeholder;
            if (slot.raf) { cancelAnimationFrame(slot.raf); slot.raf = null; }

            const outgoing = slot.layers[slot.current];
            slot.current = 1 - slot.current;
            const incoming = slot.layers[slot.current];
            const dir = rollDirection;
            const travel = slot.travel;

            // Stage the incoming layer while it is invisible and
            // untransitioned: new text, final size, start offset.
            incoming.style.transition = 'none';
            incoming.style.opacity = '0';
            incoming.style.transform = `translate3d(0, ${dir * travel}px, 0)`;
            incoming.classList.toggle('is-placeholder', placeholder);
            applySizedText(incoming.firstElementChild, text, slot.isActive, placeholder, slot.sizeCap);
            incoming.classList.add('is-current');
            outgoing.classList.remove('is-current');
            void incoming.offsetHeight; // commit the staged state

            slot.raf = requestAnimationFrame(() => {
                slot.raf = null;
                incoming.style.transition = '';
                outgoing.style.transition = '';
                incoming.style.opacity = text ? String(placeholder ? 1 : slot.opacity) : '0';
                incoming.style.transform = 'translate3d(0, 0, 0)';
                outgoing.style.opacity = '0';
                outgoing.style.transform = `translate3d(0, ${-dir * travel}px, 0)`;
            });
        }

        function refitCurrentLines() {
            layoutSlots();
            Object.values(slots).forEach(slot => {
                if (!slot.text || slot.placeholder) return;
                applySizedText(currentLayer(slot).firstElementChild, slot.text, slot.isActive, false, slot.sizeCap);
            });
        }

        let resizeTimer = null;
        let resizeRecheckTimer = null;
        function scheduleRefit() {
            clearTimeout(resizeTimer);
            clearTimeout(resizeRecheckTimer);
            resizeTimer = setTimeout(() => { refitCurrentLines(); fitTitle(); }, TIMING.RESIZE_DEBOUNCE_MS);
            // Mobile browsers can report stale dimensions right after a
            // rotation event, so double-check shortly after too.
            resizeRecheckTimer = setTimeout(() => { refitCurrentLines(); fitTitle(); }, TIMING.RESIZE_RECHECK_MS);
        }
        window.addEventListener('resize', scheduleRefit);
        window.addEventListener('orientationchange', scheduleRefit);

        // ---------- Now-playing title: fit, and marquee-scroll if it still
        // doesn't fit ----------
        const titleEl = document.getElementById('now-playing-title');
        const titleInnerEl = document.getElementById('now-playing-title-inner');
        const TITLE_MAX = 15, TITLE_MIN = 9;
        const MARQUEE_PX_PER_SEC = 38;
        const MARQUEE_TRAVEL_FRACTION = 0.88;
        let currentTitleText = '';

        const TITLE_LETTER_SPACING = 0.2;

        function measureTitleWidthAtRef(text) {
            measureCtx.font = `700 ${REF_SIZE}px 'Montserrat', sans-serif`;
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

        let titleSwapTimer = null;
        function writeTitle(title, artist) {
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

        // Title changes fade out, swap, fade in (first appearance and a
        // clear just fade). The swap happens while it is invisible, so
        // the marquee/size re-layout is never seen.
        function setTitle(title, artist) {
            const text = artist ? `${title} • ${artist}` : title;
            if (text === currentTitleText) return;
            const hadTitle = !!currentTitleText;
            currentTitleText = text;
            clearTimeout(titleSwapTimer);
            if (!hadTitle) {
                titleEl.classList.add('swapping');
                writeTitle(title, artist);
                void titleEl.offsetHeight;
                titleEl.classList.remove('swapping');
                return;
            }
            titleEl.classList.add('swapping');
            titleSwapTimer = setTimeout(() => {
                if (currentTitleText !== text) return;
                writeTitle(title, artist);
                titleEl.classList.remove('swapping');
            }, TIMING.TITLE_SWAP_MS);
        }

        // =====================================================================
        // Progress ring / seek
        // =====================================================================
        const ringSvg = document.getElementById('progress-ring');
        const ringGroup = document.getElementById('progress-ring-group');
        const ringBg = document.getElementById('progress-track-bg');
        const ringFill = document.getElementById('progress-track-fill');
        const ringHit = document.getElementById('progress-hit');
        const ringThumb = document.getElementById('progress-thumb');
        const controlsBarEl = document.getElementById('controls-bar');

        const RING_MARGIN = 6;
        const RING_RADIUS = 34;
        const RING_STEPS = 192;
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

        // The path is sampled once per layout; every per-frame position
        // lookup afterwards is a cheap linear interpolation between two
        // samples instead of a getPointAtLength() call. That is what makes
        // updating the ring on *every* animation frame affordable on a
        // low-end head unit.
        function buildRingSamples() {
            ringSamples = [];
            if (!ringTotalLength) return;
            for (let i = 0; i <= RING_STEPS; i++) {
                const len = (i / RING_STEPS) * ringTotalLength;
                const pt = ringFill.getPointAtLength(len);
                ringSamples.push({ x: pt.x, y: pt.y, len: len });
            }
        }

        function pointAtRatio(ratio) {
            const n = ringSamples.length - 1;
            if (n < 1) return { x: 0, y: 0 };
            const f = ratio * n;
            const i = Math.min(n - 1, Math.max(0, Math.floor(f)));
            const t = f - i;
            const a = ringSamples[i], b = ringSamples[i + 1];
            return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
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
            setProgressVisual(currentDisplayRatio());
        }

        function currentDisplayRatio() {
            return trackDurationMs > 0 ? currentProgressMs() / trackDurationMs : 0;
        }

        if (window.ResizeObserver) {
            new ResizeObserver(() => layoutRing()).observe(controlsBarEl);
        } else {
            window.addEventListener('resize', layoutRing);
        }

        function setProgressVisual(ratio) {
            ratio = Math.min(1, Math.max(0, ratio || 0));
            if (Math.abs(ratio - lastRingRatio) < 0.0003) return;
            lastRingRatio = ratio;
            if (!ringTotalLength) return;
            const filledLen = ratio * ringTotalLength;
            ringFill.setAttribute('stroke-dasharray', `${filledLen} ${ringTotalLength}`);
            const pt = pointAtRatio(ratio);
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

        // Live drag: the ring and the lyric lines both read from
        // currentProgressMs(), which returns seekPositionMs while
        // isSeeking - so the lyrics follow the thumb in the very same
        // frame the thumb moves, playing or paused, with no poll involved.
        function updateSeekFromEvent(e) {
            if (!trackDurationMs) return;
            const p = ringLocalPointFromEvent(e);
            const ratio = ratioFromLocalPoint(p.x, p.y);
            seekPositionMs = Math.round(ratio * trackDurationMs);
            setProgressVisual(ratio);
            syncLyricsToProgress(seekPositionMs);
        }

        function startSeek(e) {
            if (!trackDurationMs || !cachedTrackId) return;
            if (e.button !== undefined && e.button !== 0) return;
            isSeeking = true;
            ringSvg.classList.add('seeking');
            if (e.pointerId != null && ringHit.setPointerCapture) {
                try { ringHit.setPointerCapture(e.pointerId); } catch (err) {}
            }
            updateSeekFromEvent(e);
            e.preventDefault();
        }

        let seekSeq = 0;
        function endSeek() {
            if (!isSeeking) return;
            const target = seekPositionMs;
            isSeeking = false;
            ringSvg.classList.remove('seeking');
            // Commit the drag position as the display anchor immediately,
            // and hold it against poll responses until Spotify reports a
            // position that agrees with it (within tolerance, accounting
            // for elapsed playback) or the hold window passes. A fixed
            // short grace was the old bug: Spotify Connect's progress_ms
            // routinely lags 1-3 s, so the first poll after a short grace
            // still carried the pre-seek position and dragged the ring back.
            setAnchor(target);
            syncLyricsToProgress(target);
            assertLocal('seek', { progressMs: target, holdMs: TIMING.SEEK_HOLD_MS });
            sendSeek(target);
        }

        async function sendSeek(positionMs) {
            requestWakeLock();
            const mySeq = ++seekSeq;
            let ok = false;
            try {
                ok = await postControl({ action: 'seek', positionMs: positionMs });
            } catch (e) {
                ok = false;
            }
            if (mySeq !== seekSeq) return; // a newer seek superseded this one
            if (!ok) {
                // Spotify refused (no active device, restricted device,
                // rate limit...) - say so visibly and put the ring/lyrics
                // back where Spotify actually is instead of leaving a
                // position on screen that isn't real.
                flashSeekFailure();
                revertToServerSnapshot();
            }
            pollServer(true);
        }

        let seekFailTimer = null;
        function flashSeekFailure() {
            ringThumb.classList.add('seek-failed');
            clearTimeout(seekFailTimer);
            seekFailTimer = setTimeout(() => ringThumb.classList.remove('seek-failed'), TIMING.SEEK_FAIL_FLASH_MS);
        }

        if (window.PointerEvent) {
            ringHit.addEventListener('pointerdown', startSeek);
            ringHit.addEventListener('pointermove', (e) => { if (isSeeking) updateSeekFromEvent(e); });
            ringHit.addEventListener('pointerup', endSeek);
            ringHit.addEventListener('pointercancel', endSeek);
            ringHit.addEventListener('lostpointercapture', endSeek);
            window.addEventListener('pointerup', endSeek);
        } else {
            ringHit.addEventListener('mousedown', startSeek);
            ringHit.addEventListener('touchstart', startSeek, { passive: false });
            window.addEventListener('mousemove', (e) => { if (isSeeking) updateSeekFromEvent(e); });
            window.addEventListener('touchmove', (e) => { if (isSeeking) { updateSeekFromEvent(e); e.preventDefault(); } }, { passive: false });
            window.addEventListener('mouseup', endSeek);
            window.addEventListener('touchend', endSeek);
        }
        window.addEventListener('touchcancel', endSeek);
        window.addEventListener('blur', endSeek);

        // =====================================================================
        // Lyric line selection - runs from any progress value, regardless
        // of play state, so seeks while paused, live drags and normal
        // playback all share one path.
        // =====================================================================
        function activeIndexFor(progressMs) {
            // Lines are chosen slightly ahead of the clock: the roll takes
            // ROLL_MS, so starting it LYRIC_LEAD_MS early means the new
            // line is already there when the word actually lands.
            const t = progressMs + TIMING.LYRIC_LEAD_MS;
            let activeIndex = -1;
            for (let i = 0; i < parsedLines.length; i++) {
                if (parsedLines[i].startTimeMs <= t) activeIndex = i;
                else break;
            }
            return activeIndex;
        }

        function syncLyricsToProgress(progressMs) {
            if (!parsedLines.length) {
                if (cachedTrackId && !lyricsPending && lastActiveIndex !== -3) {
                    lastActiveIndex = -3;
                    showPlaceholder('No synced lyrics');
                }
                return;
            }
            const activeIndex = activeIndexFor(progressMs);
            if (activeIndex === lastActiveIndex) return;
            // -2/-3 = fresh track / placeholder: always roll forward.
            const direction = (lastActiveIndex < -1 || activeIndex >= lastActiveIndex) ? 1 : -1;
            lastActiveIndex = activeIndex;
            const prevText = activeIndex > 0 ? parsedLines[activeIndex - 1].words : "";
            const activeText = activeIndex >= 0 ? parsedLines[activeIndex].words : "";
            const nextText = activeIndex + 1 < parsedLines.length ? parsedLines[activeIndex + 1].words : "";
            applyLines(prevText, activeText, nextText, direction);
        }

        // =====================================================================
        // Polling (guarded against overlap / out-of-order), with three
        // clearly separated failure classes:
        //   (a) can't reach our own server        -> keep state, retry fast
        //   (b) server says `transient`           -> keep state, retry fast
        //       (expired/rejected token - already force-refreshed server
        //       side -, 403/429/5xx, malformed body, ad/podcast, no item)
        //   (c) Spotify genuinely reports nothing -> keep state until it has
        //       been confirmed EMPTY_CONFIRM_COUNT times in a row spanning
        //       EMPTY_CONFIRM_MS, AND we're CONTROL_GRACE_MS clear of any
        //       local action. Only then blank.
        // =====================================================================
        let pollInFlight = false;
        let pollSeq = 0;
        let missCount = 0;
        let transientCount = 0;
        let emptyStreak = 0;
        let emptyStreakStart = 0;
        let retryTimer = null;

        function scheduleRetry(ms) {
            clearTimeout(retryTimer);
            retryTimer = setTimeout(() => pollServer(true), ms);
        }

        function clearTrackDisplay() {
            isPlaying = false;
            updatePlayPauseIcon();
            lastActiveIndex = -2;
            cachedTrackId = "";
            parsedLines = [];
            layoutSlots();
            showPlaceholder('Nothing playing');
            lyricsPending = false;
            trackDurationMs = 0;
            setAnchor(0);
            currentTitleText = '';
            clearTimeout(titleSwapTimer);
            titleEl.classList.add('swapping');
            titleSwapTimer = setTimeout(() => {
                if (currentTitleText) return;
                titleInnerEl.textContent = '';
                titleInnerEl.classList.remove('marquee');
                titleEl.classList.remove('marquee-active');
            }, TIMING.TITLE_SWAP_MS);
            document.body.style.backgroundColor = '#121212';
            releaseLocal();
            if (!isSeeking) setProgressVisual(0);
        }

        // Apply a server progress value gently: tiny disagreements (a
        // poll's worth of latency, Spotify's own reporting jitter) are
        // eased out over a few polls so the ring never visibly hops;
        // large ones (a seek made on another device) snap.
        function applyServerProgress(serverProgressNow) {
            const ours = currentProgressMs();
            const delta = serverProgressNow - ours;
            if (Math.abs(delta) > TIMING.DRIFT_SNAP_MS || anchorTime === 0) {
                setAnchor(serverProgressNow);
            } else {
                setAnchor(ours + delta * TIMING.DRIFT_EASE);
            }
        }

        async function pollServer(force) {
            if (pollInFlight && !force) return;
            pollInFlight = true;
            const mySeq = ++pollSeq;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), TIMING.FETCH_TIMEOUT_MS);

            try {
                const fetchStart = nowMs();
                const have = cachedTrackId && !lyricsPending ? cachedTrackId : '';
                const res = await fetch(`/api/now-playing?t=${Date.now()}&have=${encodeURIComponent(have)}`, { signal: controller.signal });
                const data = await res.json();
                const fetchEnd = nowMs();

                if (mySeq !== pollSeq) return; // a newer response already landed

                const oneWayLatency = (fetchEnd - fetchStart) / 2;
                missCount = 0;

                if (data.trackId) {
                    transientCount = 0;
                    emptyStreak = 0;

                    // Progress as of *now*, compensating for the half round
                    // trip since Spotify measured it.
                    const serverProgressNow = (data.progressMs || 0) + (data.isPlaying ? oneWayLatency : 0);
                    serverSnap.trackId = data.trackId;
                    serverSnap.progressMs = serverProgressNow;
                    serverSnap.isPlaying = !!data.isPlaying;
                    serverSnap.at = nowMs();
                    serverSnap.valid = true;

                    const verdict = reconcileLocal(data);
                    if (verdict === 'hold') {
                        // Spotify hasn't caught up with what we just told
                        // it to do. Our own state stays authoritative; ask
                        // again soon.
                        if (localAuth.kind !== 'skip') {
                            trackDurationMs = data.durationMs || trackDurationMs;
                            setTitle(data.title, data.artist);
                        }
                        scheduleRetry(TIMING.RETRY_MS);
                        return;
                    }

                    const isNewTrack = cachedTrackId !== data.trackId;
                    trackDurationMs = data.durationMs || 0;
                    setTitle(data.title, data.artist);

                    if (isNewTrack) {
                        cachedTrackId = data.trackId;
                        parsedLines = data.lines || [];
                        lyricsPending = !!data.lyricsPending;
                        lastActiveIndex = -2;
                        layoutSlots();
                        if (!parsedLines.length) applyLines('', '', '', 1);
                        isPlaying = !!data.isPlaying;
                        setAnchor(serverProgressNow);
                        updatePlayPauseIcon();

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
                    } else {
                        // Same track. Lyrics may have just finished loading
                        // in the background - pick them up without touching
                        // anything else on screen.
                        if (lyricsPending && !data.lyricsPending && Array.isArray(data.lines)) {
                            parsedLines = data.lines;
                            lyricsPending = false;
                            lastActiveIndex = -2;
                            layoutSlots();
                        }
                        const wasPlaying = isPlaying;
                        isPlaying = !!data.isPlaying;
                        if (wasPlaying !== isPlaying) {
                            // Play state changed on another device: anchor
                            // where Spotify says, no easing.
                            setAnchor(serverProgressNow);
                        } else {
                            applyServerProgress(serverProgressNow);
                        }
                        updatePlayPauseIcon();
                    }

                    // Land on the right line right now (playing or paused)
                    // rather than waiting a frame.
                    if (!isSeeking) syncLyricsToProgress(currentProgressMs());

                    if (lyricsPending) scheduleRetry(TIMING.RETRY_MS);
                } else if (data.transient) {
                    // Class (b). Not a statement that playback stopped.
                    // Keep everything exactly as it is and retry sooner.
                    transientCount++;
                    emptyStreak = 0;
                    const wait = data.retryMs ? Math.max(TIMING.RETRY_MS, Math.min(data.retryMs, 5000)) : TIMING.RETRY_MS;
                    if (transientCount <= TIMING.RETRY_MAX || data.retryMs) scheduleRetry(wait);
                } else {
                    // Class (c). A genuine "no active session" from Spotify.
                    transientCount = 0;
                    const t = nowMs();
                    if (emptyStreak === 0) emptyStreakStart = t;
                    emptyStreak++;

                    if (localAuth.active && localAuth.kind === 'skip' && t <= localAuth.expiresAt) {
                        // Skipping past the end of a queue / between tracks
                        // often reads as "nothing playing" for a moment.
                        scheduleRetry(TIMING.RETRY_MS);
                        return;
                    }

                    const withinControlGrace = (t - lastActionAt) < TIMING.CONTROL_GRACE_MS;
                    const confirmedEnough = emptyStreak >= TIMING.EMPTY_CONFIRM_COUNT &&
                                            (t - emptyStreakStart) >= TIMING.EMPTY_CONFIRM_MS;
                    if (cachedTrackId && (withinControlGrace || !confirmedEnough)) {
                        scheduleRetry(TIMING.RETRY_MS);
                        return;
                    }
                    if (cachedTrackId || isPlaying || trackDurationMs) clearTrackDisplay();
                    emptyStreak = 0;
                }
            } catch (e) {
                // Class (a). Our own server is unreachable / timed out.
                missCount++;
                if (missCount <= TIMING.RETRY_MAX) scheduleRetry(TIMING.RETRY_MS);
            } finally {
                clearTimeout(timeoutId);
                if (mySeq === pollSeq) pollInFlight = false;
            }
        }

        layoutRing();
        // Something is on screen from the very first frame - never a
        // black page while the first Spotify round trip is in flight.
        layoutSlots();
        showPlaceholder('Connecting');
        setInterval(() => pollServer(false), TIMING.POLL_MS);
        pollServer(true);

        // =====================================================================
        // Animation loop: every frame, ring + lyrics from the same
        // currentProgressMs(). While paused that value is constant, so the
        // ring stays frozen at the exact position and the lines stay on
        // the active line by construction. While dragging it is the drag
        // position. Local authority (pending play/pause/seek/skip) is
        // expired here too so a stalled poll can't hold it open forever.
        // =====================================================================
        function animationLoop() {
            if (localAuth.active && nowMs() > localAuth.expiresAt) releaseLocal();

            const progress = currentProgressMs();
            if (!isSeeking && trackDurationMs > 0) {
                setProgressVisual(progress / trackDurationMs);
            }
            if (!isSeeking && parsedLines.length > 0) {
                syncLyricsToProgress(progress);
            }
            requestAnimationFrame(animationLoop);
        }
        requestAnimationFrame(animationLoop);
    </script>
    {% endif %}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# One keep-alive HTTP session for every outbound call (Spotify + LRCLIB).
# A bare requests.get() opens a brand-new TCP+TLS connection every time,
# which on a 400 ms poll cadence added a visible 50-150 ms to every single
# poll and every control tap. requests.Session reuses connections.
# ---------------------------------------------------------------------------
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "InCarLyricsApp/1.0"})

SPOTIFY_OK = (200, 202, 204)


def _spotify_error(res):
    """Short, stable error code for a failed Spotify call."""
    reason = ""
    try:
        body = res.json() or {}
        err = body.get("error") or {}
        if isinstance(err, dict):
            reason = err.get("reason") or err.get("message") or ""
    except Exception:
        pass
    code = f"spotify_{res.status_code}"
    if reason:
        code += f":{str(reason)[:60]}"
    return code


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
        res = HTTP.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {auth_base64}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            },
            timeout=8
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
        res = HTTP.post(
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
    on one display line, then rebalance so no chunk is left holding a
    single lonely word (the client shrinks font size to fit whatever lands
    on a line, so a soft overrun is far less noticeable than a one-word
    display line)."""
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
    """Split any line much longer than a comfortable display line into
    several timed sub-lines with proportionally interpolated timestamps."""
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
        search_res = HTTP.get(
            "https://lrclib.net/api/search",
            params={"q": f"{cleaned_name} {artist_name}"},
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

# ---------------------------------------------------------------------------
# Lyrics cache, filled in the background.
#
# The old code fetched LRCLIB synchronously inside /api/now-playing the
# first time a track was seen - so the very poll that announces a new song
# stalled for up to the LRCLIB timeout (4 s) before the client could show
# the title, colour or ring. Now the first poll for a new track returns its
# metadata immediately with `lyricsPending: true`, a daemon thread fetches
# the lyrics, and a following poll delivers them. Lyrics for a track never
# change, so LRCLIB is still hit at most once per track id.
# ---------------------------------------------------------------------------
LYRICS_CACHE = {}          # track_id -> list of lines, or _PENDING while fetching
LYRICS_CACHE_MAX = 100
LYRICS_LOCK = threading.Lock()
_PENDING = object()

def _fetch_lyrics_into_cache(track_id, track_name, artist_name):
    lines = []
    try:
        lines = fetch_synced_lyrics(track_name, artist_name)
    except Exception:
        lines = []
    finally:
        with LYRICS_LOCK:
            LYRICS_CACHE[track_id] = lines

def get_cached_lyrics(track_id, track_name, artist_name):
    """Returns (lines, pending). `lines` is [] while pending."""
    if not track_id:
        return [], False

    with LYRICS_LOCK:
        cached = LYRICS_CACHE.get(track_id)
        if cached is _PENDING:
            return [], True
        if cached is not None:
            return cached, False
        # Evict the oldest *finished* entry if we're full.
        if len(LYRICS_CACHE) >= LYRICS_CACHE_MAX:
            for k in list(LYRICS_CACHE.keys()):
                if LYRICS_CACHE[k] is not _PENDING:
                    LYRICS_CACHE.pop(k, None)
                    break
        LYRICS_CACHE[track_id] = _PENDING

    t = threading.Thread(
        target=_fetch_lyrics_into_cache,
        args=(track_id, track_name, artist_name),
        daemon=True
    )
    t.start()
    return [], True


@app.route('/api/control', methods=['POST'])
def control():
    token = get_valid_token()
    if not token:
        return jsonify({"success": False, "error": "not_logged_in"})

    payload = request.get_json(silent=True) or {}
    action = payload.get('action')
    headers = {"Authorization": f"Bearer {token}"}

    def with_refresh(call):
        """Run a Spotify call; on 401 force one token refresh and retry."""
        res = call(headers)
        if res.status_code == 401:
            fresh = get_valid_token(force=True)
            if fresh:
                res = call({"Authorization": f"Bearer {fresh}"})
        return res

    try:
        if action in ('play', 'pause'):
            # The client tells us the exact target state it already flipped
            # to optimistically - no extra state-read round trip, no race.
            res = with_refresh(lambda h: HTTP.put(
                f"https://api.spotify.com/v1/me/player/{action}", headers=h, timeout=5))
            if res.status_code in SPOTIFY_OK:
                return jsonify({"success": True})
            return jsonify({"success": False, "error": _spotify_error(res), "status": res.status_code})

        elif action in ('next', 'previous'):
            res = with_refresh(lambda h: HTTP.post(
                f"https://api.spotify.com/v1/me/player/{action}", headers=h, timeout=5))
            if res.status_code in SPOTIFY_OK:
                return jsonify({"success": True})
            return jsonify({"success": False, "error": _spotify_error(res), "status": res.status_code})

        elif action == 'seek':
            position_ms = payload.get('positionMs')
            try:
                position_ms = max(0, int(position_ms))
            except (TypeError, ValueError):
                return jsonify({"success": False, "error": "bad_position"})
            # The status is checked, not fire-and-forget: 403 (restricted
            # device / premium required), 404 (no active device) and 429
            # are all real, common ways a seek silently "does nothing".
            res = with_refresh(lambda h: HTTP.put(
                "https://api.spotify.com/v1/me/player/seek",
                params={"position_ms": position_ms}, headers=h, timeout=5))
            if res.status_code in SPOTIFY_OK:
                return jsonify({"success": True, "positionMs": position_ms})
            return jsonify({"success": False, "error": _spotify_error(res), "status": res.status_code})
    except Exception:
        return jsonify({"success": False, "error": "network_error"})

    return jsonify({"success": False, "error": "unknown_action"})


def _transient(**extra):
    body = {"isPlaying": False, "trackId": None, "transient": True}
    body.update(extra)
    return jsonify(body)

def _empty():
    # Spotify itself confirmed there's no active session. The client still
    # applies its own confirmation rules before it ever blanks the screen.
    return jsonify({"isPlaying": False, "trackId": None})

@app.route('/api/now-playing')
def now_playing():
    # Three distinct outcomes, so the client can treat them differently:
    #   - a track                      -> normal payload
    #   - {"transient": true}          -> a hiccup (network, token, 403/429/
    #                                     5xx, malformed body, ad/podcast,
    #                                     item missing). NOT "stopped".
    #   - {"trackId": null} (no flag)  -> Spotify genuinely reports no active
    #                                     session (204 / empty player object)
    token = get_valid_token()
    if not token:
        return _transient(reason="no_token")

    have = request.args.get('have', '')

    def fetch_player(tok):
        return HTTP.get(
            "https://api.spotify.com/v1/me/player",
            params={"additional_types": "track,episode"},
            headers={"Authorization": f"Bearer {tok}"},
            timeout=4
        )

    try:
        spotify_t0 = time.time()
        player_res = fetch_player(token)
        if player_res.status_code == 401:
            # Token rejected although we believed it valid (clock skew,
            # revoked early). One forced refresh-and-retry, right now.
            fresh_token = get_valid_token(force=True)
            if fresh_token:
                spotify_t0 = time.time()
                player_res = fetch_player(fresh_token)
    except Exception:
        return _transient(reason="network")

    if player_res.status_code == 204:
        return _empty()

    if player_res.status_code == 429:
        retry_ms = 1000
        try:
            retry_ms = int(float(player_res.headers.get('Retry-After', '1'))) * 1000
        except (TypeError, ValueError):
            pass
        return _transient(reason="rate_limited", retryMs=max(250, min(retry_ms, 10000)))

    if not player_res.ok:
        return _transient(reason=f"spotify_{player_res.status_code}")

    try:
        player = player_res.json()
    except Exception:
        return _transient(reason="bad_json")

    if not player or not isinstance(player, dict):
        return _empty()

    item = player.get('item')
    playing_type = player.get('currently_playing_type') or 'track'
    if item is None or not isinstance(item, dict):
        # A player object with no item: mid-transition between tracks, an
        # ad break, or a private/unavailable item. Not proof of a stop.
        return _transient(reason="no_item")
    if playing_type not in ('track', 'episode'):
        return _transient(reason=playing_type)

    track_id = item.get('id') or ""
    track_name = item.get('name') or ""
    artists = item.get('artists') or []
    if artists and isinstance(artists[0], dict):
        artist_name = artists[0].get('name', '')
    else:
        show = item.get('show') or {}
        artist_name = show.get('name', '') if isinstance(show, dict) else ""

    if not track_name or not track_id:
        return _transient(reason="no_track")

    album = item.get('album') or item.get('show') or {}
    images = album.get('images') or item.get('images') or []
    album_art = images[0].get('url', '') if images and isinstance(images[0], dict) else ""

    duration_ms = item.get('duration_ms') or 0
    progress_ms = player.get('progress_ms') or 0
    # Spotify measured progress_ms when it built its response, about half
    # a server<->Spotify round trip ago; the browser compensates for its
    # own half round trip to us on top of this.
    if player.get('is_playing'):
        progress_ms += int((time.time() - spotify_t0) * 500)

    body = {
        "isPlaying": bool(player.get('is_playing', False)),
        "progressMs": progress_ms,
        "durationMs": duration_ms,
        "title": track_name,
        "artist": artist_name,
        "albumArt": album_art,
        "trackId": track_id,
        "lyricsPending": False
    }

    if playing_type == 'episode' or not artist_name:
        # Podcasts etc: no synced lyrics to look for.
        body["lines"] = []
        return jsonify(body)

    lines, pending = get_cached_lyrics(track_id, track_name, artist_name)
    body["lyricsPending"] = pending
    # The client already holds the lines for the track it names in `have`
    # - don't re-send a multi-KB lyric list on every 400 ms poll.
    if pending or have != track_id:
        body["lines"] = lines
    return jsonify(body)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)