import math
import shutil
import subprocess
from pathlib import Path

from music21 import (
    stream,
    note,
    instrument,
    tempo,
    meter,
)

def salvar_midi(
    melodia,
    caminho,
    duracoes=None,
    bpm=120,
    perfil="aventura",
    incluir_acompanhamento=True,
):
    # Salva a melodia em MIDI com ritmo e acompanhamento opcionais.
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if not melodia:
        raise ValueError("A melodia não pode estar vazia.")

    if bpm <= 0:
        raise ValueError("O BPM precisa ser positivo.")

    if duracoes is None:
        duracoes = [0.5] * len(melodia)

    if len(duracoes) != len(melodia):
        raise ValueError(
            "A quantidade de durações deve corresponder às notas."
        )

    if any(float(d) <= 0 for d in duracoes):
        raise ValueError("Todas as durações precisam ser positivas.")

    score = stream.Score()
    score.insert(0, tempo.MetronomeMark(number=bpm))
    score.insert(0, meter.TimeSignature("4/4"))

    # Melodia principal.
    linha = stream.Part()
    linha.insert(0, instrument.Flute())
    posicao = 0.0

    for altura, duracao in zip(melodia, duracoes):
        altura = int(altura)

        if not 0 <= altura <= 127:
            raise ValueError(f"Altura MIDI fora do intervalo: {altura}")

        nova_nota = note.Note(altura)
        nova_nota.quarterLength = float(duracao)
        linha.insert(posicao, nova_nota)
        posicao += float(duracao)

    score.insert(0, linha)

    # Acompanhamento de baixo.
    if incluir_acompanhamento:
        baixo = stream.Part()
        baixo.insert(0, instrument.AcousticBass())

        raiz = _estimar_raiz(melodia)
        progressao = _progressao(perfil)
        compassos = max(1, math.ceil(posicao / 4.0))

        for compasso in range(compassos):
            grau = progressao[compasso % len(progressao)]
            altura = raiz + grau - 12

            while altura < 36:
                altura += 12

            while altura > 55:
                altura -= 12

            inicio = compasso * 4.0
            duracao = min(4.0, posicao - inicio)

            if duracao <= 0:
                continue

            nota_baixo = note.Note(altura)
            nota_baixo.quarterLength = duracao
            baixo.insert(inicio, nota_baixo)

        score.insert(0, baixo)

    score.write("midi", fp=str(caminho))
    return caminho


def _estimar_raiz(melodia):
    # Estima uma classe de altura pela frequência no material gerado.
    contagens = [0] * 12

    for altura in melodia:
        contagens[int(altura) % 12] += 1

    classe = max(range(12), key=lambda i: contagens[i])
    return 48 + classe


def _progressao(perfil):
    # Progressões simples definidas manualmente por perfil.
    perfis = {
        "aventura": [0, 7, 9, 5],
        "suspense": [0, 3, 6, 7],
        "exploracao": [0, 5, 7, 0],
        "arcade": [0, 5, 3, 7],
    }

    return perfis.get(perfil, perfis["aventura"])


def midi_para_wav(
    caminho_midi,
    caminho_wav,
    soundfont="soundfont.sf2",
):
    # Converte MIDI para WAV usando o programa FluidSynth.
    midi = Path(caminho_midi)
    wav = Path(caminho_wav)
    fonte = Path(soundfont)

    if not midi.exists():
        raise FileNotFoundError(f"MIDI não encontrado: {midi}")

    if not fonte.exists():
        raise FileNotFoundError(
            f"SoundFont não encontrada: {fonte}"
        )

    fluidsynth = shutil.which("fluidsynth")

    if fluidsynth is None:
        raise FileNotFoundError(
            "FluidSynth não está instalado ou não está no PATH."
        )

    wav.parent.mkdir(parents=True, exist_ok=True)

    comando = [
        fluidsynth,
        "-ni",
        "-g", "1",
        "-r", "44100",
        "-F", str(wav),
        str(fonte),
        str(midi),
    ]

    subprocess.run(comando, check=True, capture_output=True, text=True)

    return wav