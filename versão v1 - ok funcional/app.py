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

app = Flask(__name__)

@app.route('/')
def index():
    # Verifica se o template existe
    template_path = os.path.join(app.root_path, 'templates', 'index.html')
    if not os.path.exists(template_path):
        return "Template 'index.html' não encontrado na pasta 'templates'. Verifique a estrutura do projeto.", 500
    return render_template('index.html')

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        video_url = data.get('url')
        language_code = data.get('language_code')  # Novo parâmetro opcional

        if not video_url:
            return jsonify({'error': 'URL do vídeo não fornecida.'}), 400

        # Analisar a URL para extrair o ID do vídeo
        parsed_url = urlparse(video_url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            query = parse_qs(parsed_url.query)
            video_id = query.get('v')
            if not video_id:
                return jsonify({'error': 'ID do vídeo não encontrado na URL fornecida.'}), 400
            video_id = video_id[0]
        elif parsed_url.hostname in ['youtu.be']:
            video_id = parsed_url.path.lstrip('/')
        else:
            return jsonify({'error': 'URL do YouTube inválida.'}), 400

        # Listar todas as transcrições disponíveis
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        if language_code:
            try:
                transcript = transcript_list.find_transcript([language_code])
            except NoTranscriptFound:
                # Tentar pegar a transcrição automática se a manual não estiver disponível
                transcript = transcript_list.find_generated_transcript([language_code])
        else:
            # Tentar encontrar uma transcrição em português ou inglês
            try:
                transcript = transcript_list.find_transcript(['pt', 'en'])
            except CouldNotRetrieveTranscript:
                # Se não encontrar nas línguas especificadas, pegar a primeira disponível
                transcript = transcript_list.find_transcript(transcript_list._transcripts.keys())

        # Obter a transcrição
        transcript_data = transcript.fetch()
        return jsonify(transcript_data)

    except TranscriptsDisabled:
        return jsonify({'error': 'Transcrições desabilitadas para este vídeo.'}), 400
    except NoTranscriptFound:
        return jsonify({'error': 'Nenhuma transcrição encontrada para este vídeo.'}), 400
    except VideoUnavailable:
        return jsonify({'error': 'Vídeo indisponível.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcripts', methods=['POST'])
def list_transcripts():
    try:
        data = request.get_json()
        video_url = data.get('url')

        if not video_url:
            return jsonify({'error': 'URL do vídeo não fornecida.'}), 400

        # Analisar a URL para extrair o ID do vídeo
        parsed_url = urlparse(video_url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            query = parse_qs(parsed_url.query)
            video_id = query.get('v')
            if not video_id:
                return jsonify({'error': 'ID do vídeo não encontrado na URL fornecida.'}), 400
            video_id = video_id[0]
        elif parsed_url.hostname in ['youtu.be']:
            video_id = parsed_url.path.lstrip('/')
        else:
            return jsonify({'error': 'URL do YouTube inválida.'}), 400

        # Listar todas as transcrições disponíveis
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcripts_info = []

        for transcript in transcript_list:
            transcripts_info.append({
                'language': transcript.language,
                'language_iso': transcript.language_code,
                'is_generated': transcript.is_generated
            })

        return jsonify({'transcripts': transcripts_info})

    except TranscriptsDisabled:
        return jsonify({'error': 'Transcrições desabilitadas para este vídeo.'}), 400
    except NoTranscriptFound:
        return jsonify({'error': 'Nenhuma transcrição encontrada para este vídeo.'}), 400
    except VideoUnavailable:
        return jsonify({'error': 'Vídeo indisponível.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
