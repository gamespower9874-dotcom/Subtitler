# Subtitler

Pipeline open source pour sous-titrer des vidéos : extraction audio haute qualité,
transcription (Whisper / Deepgram), diarisation, traduction adaptée avec glossaire
(API xAI Grok), contrôle qualité inspiré des normes Netflix, interface Gradio.

## Installation

```bash
git clone https://github.com/<ton-compte>/subtitler.git
cd subtitler
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # puis renseigne tes clés
python -m app.ui
```

FFmpeg doit être installé (`sudo apt install ffmpeg` / `brew install ffmpeg`).
Avec Docker : `docker build -t subtitler . && docker run -p 7860:7860 --env-file .env subtitler`

## Clés API

| Variable | Usage | Obligatoire |
|---|---|---|
| `DEEPGRAM_API_KEY` | Transcription + diarisation | Si moteur Deepgram |
| `OPENAI_API_KEY` | Transcription Whisper | Si moteur Whisper |
| `XAI_API_KEY` | Traduction adaptée (Grok) | Oui |

## Feuille de route

- [ ] Séparation voix/musique (Demucs)
- [ ] Détection de langue par segment
- [ ] Agent IA : fiches de voix par personnage (audio, images, recherche web)
- [ ] Plateforme communautaire anonyme (propositions, votes)
- [ ] Export TTML et rapport QC détaillé

## Utilisation responsable

Ce logiciel ne fournit ni ne distribue de vidéos. Chaque utilisateur est responsable
d'avoir le droit de traiter et de sous-titrer les contenus qu'il manipule. Il est
réservé aux contenus légaux : tout contenu impliquant des mineurs ou non consenti est
interdit. Le logiciel est fourni sans garantie.

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md). Licence : AGPL-3.0-or-later.
