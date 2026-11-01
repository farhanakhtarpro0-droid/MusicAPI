from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import traceback
import sys

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Music API is Running Successfully!"

# 1. सर्च API (यह बिल्कुल सही काम कर रहा है)
@app.route('/search', methods=['GET'])
def search_music():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "कृपया सर्च के लिए ?q= गाने का नाम डालें"}), 400

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['ios']}}
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch10:{query}"
            info = ydl.extract_info(search_query, download=False)
            results = []
            for entry in info.get('entries', []):
                video_id = entry.get('id')
                if video_id:
                    poster_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    results.append({
                        "id": video_id,
                        "title": entry.get('title'),
                        "poster": poster_url,
                        "duration": entry.get('duration')
                    })
            return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 2. प्ले API (Cloudflare बाईपास Headers के साथ)
@app.route('/play', methods=['GET'])
def play_music():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "कृपया गाने की ID दें ?id=..."}), 400

    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.moomoo.me",
        "https://api.piped.projectsegfau.lt",
        "https://piped-api.lunar.icu",
        "https://pipedapi.smnz.de"
    ]

    # सबसे ज़रूरी बदलाव: Cloudflare के गार्ड को बाईपास करने के लिए असली ब्राउज़र की पहचान
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://piped.kavin.rocks/"
    }

    last_error = ""

    for instance in piped_instances:
        try:
            print(f"Trying API: {instance}", flush=True)
            api_url = f"{instance}/streams/{video_id}"
            
            # अब हम headers भी साथ भेज रहे हैं
            resp = requests.get(api_url, headers=headers, timeout=7) 
            
            if resp.status_code == 200:
                data = resp.json()
                audio_url = None
                
                for stream in data.get('audioStreams', []):
                    if 'mp4' in stream.get('mimeType', '') or 'm4a' in stream.get('mimeType', ''):
                        audio_url = stream.get('url')
                        break
                
                if not audio_url and data.get('audioStreams'):
                    audio_url = data['audioStreams'][0].get('url')
                    
                if audio_url:
                    print(f"SUCCESS: {instance} से ऑडियो मिल गया!", flush=True)
                    return jsonify({
                        "status": "success",
                        "id": video_id,
                        "title": data.get('title'),
                        "audio_url": audio_url,
                        "poster": data.get('thumbnailUrl')
                    })
            else:
                print(f"FAILED on {instance}: Status {resp.status_code}", flush=True)
                last_error = f"Status {resp.status_code}"
                
        except Exception as e:
            print(f"ERROR on {instance}: {str(e)}", flush=True)
            last_error = str(e)
            continue 

    return jsonify({"status": "error", "message": f"सभी बैकअप सर्वर फेल हो गए। अंतिम एरर: {last_error}"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
