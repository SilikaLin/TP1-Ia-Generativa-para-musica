import argparse
import random
from pathlib import Path
from corpus_reader import CorpusReader
from markov_chain import MarkovChain
from saida_midi import salvar_midi, midi_para_wav

ORDEM = 2
NUM_NOTAS = 256
DELAY = 150  # ms por nota
SOUNDFONT = "soundfont.sf2"  # qualquer .sf2 serve, é só pro áudio

def gerar_musica(corpus, seed, order, output_folder):
    print(f"\n=== seed={seed}, ordem={order} ===")

    markov = MarkovChain(seed, 0, order)
    markov.train(corpus)
    notas = markov.gerar(corpus, NUM_NOTAS)

    arquivo = output_folder / f"musica_order{order}_seed{seed}.mid"
    salvar_midi(notas, arquivo, DELAY)
    midi_para_wav(arquivo, arquivo.with_suffix(".wav"), SOUNDFONT)

def main():
    parser = argparse.ArgumentParser(description="Gera uma música com cadeia de Markov.")
    parser.add_argument("--seed", type=int, help="repete uma música (padrão: aleatória)")
    parser.add_argument("--ordem", type=int, default=ORDEM, help=f"padrão: {ORDEM}")
    args = parser.parse_args()

    if args.seed is not None:
        seed = args.seed
    else:
        seed = random.randrange(1_000_000)

    corpus = CorpusReader("corpus").read_corpus()

    output_folder = Path("musicas")
    output_folder.mkdir(exist_ok=True)

    gerar_musica(corpus, seed, args.ordem, output_folder)

if __name__ == "__main__":
    main()