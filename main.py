import argparse
import random
from pathlib import Path
from corpus_reader import CorpusReader
from markov_chain import MarkovChain
from saida_midi import salvar_midi, midi_para_wav

PERFIS = {
    "aventura": {
        "bpm": 132,
        "temperatura": 1.15,
        "ritmo": [0.5, 0.5, 1.0, 1.0, 2.0],
    },
    "suspense": {
        "bpm": 84,
        "temperatura": 0.85,
        "ritmo": [1.0, 1.0, 2.0, 0.5, 0.5],
    },
    "arcade": {
        "bpm": 156,
        "temperatura": 1.3,
        "ritmo": [0.25, 0.25, 0.5, 0.5, 1.0],
    },
}

def gerar_duracoes(n_notas, perfil, rng):
    # Gera durações usando as opções rítmicas do perfil.
    opcoes = PERFIS[perfil]["ritmo"]
    return [rng.choice(opcoes) for _ in range(n_notas)]

def gerar_musica(
    ordem,
    seed,
    n_notas,
    perfil,
    pasta_corpus,
    soundfont,
    gerar_wav=True,
    acompanhamento=True,
    pasta_musicas="musicas",
):
    if ordem < 1:
        raise ValueError("A ordem deve ser pelo menos 1.")

    if n_notas < 1:
        raise ValueError("A quantidade de notas deve ser positiva.")

    rng = random.Random(seed)
    configuracao = PERFIS[perfil]

    corpus = CorpusReader(pasta_corpus).carregar_corpus()

    modelo = MarkovChain(ordem=ordem, seed=seed)
    modelo.treinar(corpus)

    melodia, fallbacks = modelo.gerar_com_estatisticas(
        n_notas=n_notas,
        temperatura=configuracao["temperatura"],
        evitar_repeticao=True,
    )

    duracoes = gerar_duracoes(n_notas, perfil, rng)

    pasta = Path(pasta_musicas)
    pasta.mkdir(parents=True, exist_ok=True)

    base = f"musica_{perfil}_order{ordem}_seed{seed}"
    caminho_midi = pasta / f"{base}.mid"
    caminho_wav = pasta / f"{base}.wav"

    salvar_midi(
        melodia,
        caminho_midi,
        duracoes=duracoes,
        bpm=configuracao["bpm"],
        perfil=perfil,
        incluir_acompanhamento=acompanhamento,
    )

    print(f"\nMIDI criado: {caminho_midi}")
    print(f"Notas geradas: {len(melodia)}")
    print(f"Alturas distintas: {len(set(melodia))}")
    print(f"Contextos no modelo: {modelo.get_numero_contextos()}")
    print(f"Fallbacks durante a geração: {fallbacks}")
    print(f"Entropia média do modelo: {modelo.entropia_media():.3f}")
    print(f"Proporção de contextos determinísticos: {modelo.proporcao_contextos_deterministicos():.3f}")

    if gerar_wav:
        try:
            midi_para_wav(
                caminho_midi,
                caminho_wav,
                soundfont=soundfont,
            )
            print(f"WAV criado: {caminho_wav}")

        except (
            FileNotFoundError,
            OSError,
            RuntimeError,
            Exception,
        ) as erro:
            # O MIDI já foi salvo, mesmo se a conversão falhar.
            print(f"[aviso] Não foi possível criar o WAV: {erro}")
            print("Confira o FluidSynth e o caminho da SoundFont.")
    return caminho_midi


def main():
    parser = argparse.ArgumentParser(
        description="Gerador musical com Cadeias de Markov."
    )

    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--ordem", type=int, default=2)
    parser.add_argument("--notas", type=int, default=256)
    parser.add_argument("--perfil", choices=PERFIS.keys(), default="aventura")
    parser.add_argument("--corpus", default="corpus")
    parser.add_argument("--soundfont", default="soundfont.sf2")
    parser.add_argument("--musicas", default="musicas")
    parser.add_argument("--sem-wav", action="store_true", help="Gera somente o MIDI.")
    parser.add_argument("--sem-acompanhamento", action="store_true", help="Gera somente a melodia.")

    args = parser.parse_args()

    gerar_musica(
        ordem=args.ordem,
        seed=args.seed,
        n_notas=args.notas,
        perfil=args.perfil,
        pasta_corpus=args.corpus,
        soundfont=args.soundfont,
        gerar_wav=not args.sem_wav,
        acompanhamento=not args.sem_acompanhamento,
        pasta_musicas=args.musicas,
    )

if __name__ == "__main__":
    main()