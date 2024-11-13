import os
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

# Inicializando o Flask
app = Flask(__name__)

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        # Obter a URL do vídeo da requisição
        data = request.get_json()
        video_url = data.get('url')

        if not video_url:
            return jsonify({'error': 'URL do vídeo não fornecida.'}), 400

        # Extrair o ID do vídeo da URL
        video_id = video_url.split('v=')[1].split('&')[0]

        # Obter a transcrição do vídeo
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # Retornar a transcrição formatada
        return jsonify({'status': 'success', 'transcript': '\n'.join([t['text'] for t in transcript])})

    except TranscriptsDisabled:
        return jsonify({'error': 'Transcrições desabilitadas para este vídeo.'}), 400
    except NoTranscriptFound:
        return jsonify({'error': 'Nenhuma transcrição encontrada para este vídeo.'}), 400
    except VideoUnavailable:
        return jsonify({'error': 'Vídeo indisponível.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Garantir que o servidor Flask rode na porta correta no ambiente de produção
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
