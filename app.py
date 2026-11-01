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


# 2. प्ले API (नया Piped API बाईपास सिस्टम)
@app.route('/play', methods=['GET'])
def play_music():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "कृपया गाने की ID दें ?id=..."}), 400

    try:
        # YouTube ब्लॉक से बचने के लिए हम Piped API का सीधा इस्तेमाल करेंगे
        api_url = f"https://pipedapi.kavin.rocks/streams/{video_id}"
        resp = requests.get(api_url)
        
        if resp.status_code == 200:
            data = resp.json()
            audio_url = None
            
            # Android के लिए सबसे बेस्ट (m4a/mp4) ऑडियो लिंक ढूँढें
            for stream in data.get('audioStreams', []):
                if 'mp4' in stream.get('mimeType', '') or 'm4a' in stream.get('mimeType', ''):
                    audio_url = stream.get('url')
                    break
            
            # अगर m4a न मिले, तो लिस्ट का पहला ऑडियो लिंक ले लें
            if not audio_url and data.get('audioStreams'):
                audio_url = data['audioStreams'][0].get('url')
                
            if audio_url:
                print(f"SUCCESS: {video_id} का ऑडियो Piped API से मिल गया!", flush=True)
                return jsonify({
                    "status": "success",
                    "id": video_id,
                    "title": data.get('title'),
                    "audio_url": audio_url,
                    "poster": data.get('thumbnailUrl')
                })
                
        return jsonify({"status": "error", "message": "ऑडियो लिंक नहीं मिला (Piped API Error)"}), 404

    except Exception as e:
        print("=== PLAY ERROR ===", file=sys.stderr)
        traceback.print_exc()
        print("==================", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
