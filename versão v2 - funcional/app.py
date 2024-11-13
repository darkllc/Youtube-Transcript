# app.py

from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript
)
from urllib.parse import urlparse, parse_qs
import os
import logging

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        video_url = data.get('url')

        if not video_url:
            logger.warning('Nenhuma URL de vídeo fornecida.')
            return jsonify({'error': 'URL do vídeo não fornecida.'}), 400

        # Extrair o ID do vídeo da URL
        parsed_url = urlparse(video_url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            query = parse_qs(parsed_url.query)
            video_id = query.get('v')
            if not video_id:
                logger.warning('ID do vídeo não encontrado na URL fornecida.')
                return jsonify({'error': 'ID do vídeo não encontrado na URL fornecida.'}), 400
            video_id = video_id[0]
        elif parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path.lstrip('/')
        else:
            logger.warning('URL do YouTube inválida.')
            return jsonify({'error': 'URL do YouTube inválida.'}), 400

        logger.info(f'Buscando transcrição para o vídeo ID: {video_id}')

        # Obter a lista de transcrições disponíveis
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Tentar obter a transcrição no idioma do vídeo (Português ou Inglês)
        try:
            transcript = transcript_list.find_transcript(['pt', 'en'])
            logger.info(f'Transcrição encontrada em: {transcript.language}')
        except NoTranscriptFound:
            # Se não encontrar nas línguas especificadas, pegar a primeira disponível
            transcript = transcript_list.find_transcript(transcript_list._transcripts.keys())
            logger.info(f'Transcrição encontrada em: {transcript.language}')

        # Obter a transcrição completa
        transcript_data = transcript.fetch()
        logger.info(f'Número de segmentos de transcrição obtidos: {len(transcript_data)}')

        # Concatenar todo o texto sem marcações de tempo
        full_transcript = ' '.join([item['text'] for item in transcript_data])

        return jsonify({'transcript': full_transcript, 'status': 'success'})

    except TranscriptsDisabled:
        logger.error('Transcrições desabilitadas para este vídeo.')
        return jsonify({'error': 'Transcrições desabilitadas para este vídeo.', 'status': 'error'}), 400
    except NoTranscriptFound:
        logger.error('Nenhuma transcrição encontrada para este vídeo.')
        return jsonify({'error': 'Nenhuma transcrição encontrada para este vídeo.', 'status': 'error'}), 400
    except VideoUnavailable:
        logger.error('Vídeo indisponível.')
        return jsonify({'error': 'Vídeo indisponível.', 'status': 'error'}), 400
    except Exception as e:
        logger.exception('Ocorreu um erro inesperado.')
        return jsonify({'error': str(e), 'status': 'error'}), 500

if __name__ == '__main__':
    app.run(debug=True)