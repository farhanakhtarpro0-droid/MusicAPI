from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)

# CORS चालू कर दिया गया है
CORS(app)

@app.route('/')
def home():
    return "Music API is Running Successfully!"

# 1. सर्च API (यह तुरंत गानों की लिस्ट, नाम और पोस्टर देगा)
@app.route('/search', methods=['GET'])
def search_music():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "कृपया सर्च के लिए ?q= गाने का नाम डालें"}), 400

    # YouTube Bot Block से बचने के लिए नई सेटिंग्स (User Agent के साथ)
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # सीधे नाम के बजाय ytsearch10: लगाकर सर्च करेंगे ताकि YouTube ब्लॉक न करे
            search_query = f"ytsearch10:{query}"
            info = ydl.extract_info(search_query, download=False)
            results = []
            
            for entry in info.get('entries', []):
                video_id = entry.get('id')
                if video_id:  # सिर्फ वही डेटा लेंगे जिसमें सही ID हो
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


# 2. प्ले API (यह गाने का डायरेक्ट ऑडियो लिंक देगा)
@app.route('/play', methods=['GET'])
def play_music():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "कृपया गाने की ID दें ?id=..."}), 400

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # सबसे अच्छी ऑडियो क्वालिटी और Bot Bypass की सेटिंग
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return jsonify({
                "status": "success",
                "id": video_id,
                "title": info.get('title'),
                "audio_url": info.get('url'), # डायरेक्ट ऑडियो स्ट्रीमिंग लिंक
                "poster": info.get('thumbnail')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# सर्वर चलाने के लिए
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
