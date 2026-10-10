import shutil
import subprocess
from pathlib import Path
from music21 import stream, note, tempo

BPM = 120  # 500 ms por semínima

def salvar_midi(notas, filename, delay):
    # grava as notas num .mid, cada uma durando delay ms
    score = stream.Stream()
    score.append(tempo.MetronomeMark(number=BPM))

    quarter_length = delay / (60000 / BPM)

    for midi_note in notas:
        pitch = max(0, min(127, int(midi_note)))
        nova_nota = note.Note(pitch)
        nova_nota.quarterLength = quarter_length
        score.append(nova_nota)

    score.write("midi", fp=str(filename))
    print(f"MIDI criado: {filename}")

def midi_para_wav(midi_file, wav_file, soundfont):
    # converte o .mid em .wav com o FluidSynth
    if shutil.which("fluidsynth") is None:
        print("FluidSynth não encontrado, pulando o WAV.")
        return False

    if not Path(soundfont).exists():
        print(f"Soundfont '{soundfont}' não encontrado, pulando o WAV.")
        return False

    comando = [
        "fluidsynth", "-ni",
        "-g", "1",           # o ganho padrão (0.2) deixa o WAV baixo demais
        "-r", "44100",
        "-T", "wav",
        "-F", str(wav_file),
        str(soundfont),
        str(midi_file),
    ]

    try:
        subprocess.run(comando, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as erro:
        print(f"FluidSynth falhou em {midi_file}:\n{erro.stderr}")
        return False

    print(f"WAV criado: {wav_file}")
    return True