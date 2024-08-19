from flask import Flask, jsonify, request
from Media_Details_Extractors.vidsrc2 import Vidsrc

app = Flask(__name__)

# Route for fetching movie streams
@app.route('/vidsrc/movie', methods=['GET'])
def get_movie_streams():
    tmdb_id = request.args.get('id')

    if not tmdb_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    vidsrc = Vidsrc()
    m3u8_links = vidsrc.fetch_movie(tmdb_id)

    return jsonify({"m3u8_links": m3u8_links, "subtitles": []})

# Route for fetching TV show streams
@app.route('/vidsrc/tv', methods=['GET'])
def get_tv_streams():
    tmdb_id = request.args.get('id')
    season = request.args.get('season')
    episode = request.args.get('episode')

    if not tmdb_id or not season or not episode:
        return jsonify({"error": "Missing 'id', 'season', or 'episode' parameter"}), 400

    vidsrc = Vidsrc()
    m3u8_links = vidsrc.fetch_tv(tmdb_id, season, episode)

    return jsonify({"m3u8_links": m3u8_links, "subtitles": []})

if __name__ == '__main__':
    app.run(port=5002, debug=True)

