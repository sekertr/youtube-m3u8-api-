from flask import Flask, jsonify, request
import yt_dlp
import os
import tempfile

app = Flask(__name__)

def get_cookies_file():
    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    if not cookies_content:
        return None
    # Geçici dosyaya yaz
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name

def get_m3u8(youtube_url):
    cookies_file = get_cookies_file()
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'format': 'best[protocol=m3u8_native]/best',
    }
    
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        formats = info.get('formats', [])
        
        for f in formats:
            if f.get('protocol') in ('m3u8_native', 'm3u8'):
                if f.get('url'):
                    return f['url']
        
        if info.get('manifest_url'):
            return info['manifest_url']
            
        raise Exception("M3U8 URL bulunamadı")

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'YouTube M3U8 Proxy API'})

@app.route('/get-m3u8')
def api_get_m3u8():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'url parametresi gerekli'}), 400
    
    if 'youtube.com' not in url and 'youtu.be' not in url:
        return jsonify({'error': 'Sadece YouTube URLleri desteklenir'}), 400
    
    try:
        m3u8_url = get_m3u8(url)
        return jsonify({'success': True, 'm3u8': m3u8_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
