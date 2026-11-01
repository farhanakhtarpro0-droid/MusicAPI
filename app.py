from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)

# CORS चालू कर दिया गया है
CORS(app)

@app.route('/')
def home():
    return "Music API is Running Successfully!"

# 1. सर्च API
@app.route('/search', methods=['GET'])
def search_music():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "कृपया सर्च के लिए ?q= गाने का नाम डालें"}), 400

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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


# 2. प्ले API (नए Android Bypass और स्मार्ट URL फाइंडर के साथ)
@app.route('/play', methods=['GET'])
def play_music():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "कृपया गाने की ID दें ?id=..."}), 400

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best', # m4a फॉर्मेट Android के लिए सबसे अच्छा है
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        # यह सबसे ज़रूरी सेटिंग है जो YouTube को बताएगी कि यह एक Android डिवाइस है:
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # पहले सीधा ऑडियो URL ढूँढने की कोशिश करेंगे
            audio_url = info.get('url')
            
            # अगर सीधा URL नहीं मिला, तो छुपे हुए 'formats' लिस्ट में से सिर्फ ऑडियो वाला लिंक निकालेंगे
            if not audio_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f.get('url')
                        break 
                        
            if audio_url:
                return jsonify({
                    "status": "success",
                    "id": video_id,
                    "title": info.get('title'),
                    "audio_url": audio_url,
                    "poster": info.get('thumbnail')
                })
            else:
                return jsonify({"status": "error", "message": "ऑडियो लिंक नहीं मिला"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# सर्वर चलाने के लिए
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
