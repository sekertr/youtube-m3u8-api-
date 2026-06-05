from flask import Flask, jsonify, request, redirect
import yt_dlp
import os
import tempfile
import base64

app = Flask(__name__)

def get_cookies_file():
    cookies_b64 = os.environ.get('YOUTUBE_COOKIES_B64')
    if cookies_b64:
        tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False)
        tmp.write(base64.b64decode(cookies_b64))
        tmp.close()
        return tmp.name
    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    if cookies_content:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        tmp.write(cookies_content)
        tmp.close()
        return tmp.name
    return None

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

# ← YENİ: /https://... şeklinde gelen istekleri yakala
@app.route('/<path:youtube_url>')
def proxy_catch(youtube_url):
    if not youtube_url.startswith('http'):
        return jsonify({'error': 'Geçersiz URL'}), 400
    if 'youtube.com' not in youtube_url and 'youtu.be' not in youtube_url:
        return jsonify({'error': 'Sadece YouTube URLleri desteklenir'}), 400
    try:
        m3u8_url = get_m3u8(youtube_url)
        return redirect(m3u8_url, 302)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
