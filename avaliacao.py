import contextlib
import csv
import io
import math
import statistics
from collections import Counter, defaultdict
from corpus_reader import CorpusReader
from main import NUM_NOTAS
from markov_chain import MarkovChain

ORDENS = [1, 2, 3]
SEEDS = range(100, 110)

CAMPOS = [
    "mem_4", "mem_8", "maior_trecho", "dist_altura",
    "dist_intervalo", "fallbacks", "entropia", "deterministicos",
]

def gerar(corpus, ordem, seed):
    markov = MarkovChain(seed, 0, ordem)
    with contextlib.redirect_stdout(io.StringIO()):  # esconde o print do treino
        markov.train(corpus)

    notas = markov.gerar(corpus, NUM_NOTAS)
    return notas, markov.fallbacks, markov.chain

def ngramas(seq, n):
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]

def taxa_memorizacao(gerado, corpus, n):
    # que fração dos n-gramas gerados já aparece no corpus
    conhecidos = set()
    for seq in corpus:
        conhecidos.update(ngramas(seq, n))

    gerados = ngramas(gerado, n)
    achados = sum(g in conhecidos for g in gerados)
    return achados / len(gerados)

def maior_trecho_copiado(gerado, corpus):
    # maior sequência de notas que a música copia de alguma voz do corpus
    return max(trecho_comum(gerado, seq) for seq in corpus)

def trecho_comum(gerado, seq):
    posicoes = defaultdict(list)
    for j, nota in enumerate(seq):
        posicoes[nota].append(j)

    melhor = 0
    anterior = {}
    for nota in gerado:
        atual = {}
        for j in posicoes[nota]:
            atual[j] = anterior.get(j - 1, 0) + 1
        melhor = max(melhor, max(atual.values(), default=0))
        anterior = atual
    return melhor

def intervalos(seq):
    return [b - a for a, b in zip(seq, seq[1:])]

def distancia(a, b):
    # distância de variação total entre as distribuições de a e b
    ca, cb = Counter(a), Counter(b)
    soma = 0
    for k in set(ca) | set(cb):
        soma += abs(ca[k] / len(a) - cb[k] / len(b))
    return 0.5 * soma

def estatisticas_modelo(chain):
    entropias = []
    for trans in chain.values():
        entropias.append(sum(p * math.log2(1 / p) for p in trans.values()))

    deterministicos = sum(len(trans) == 1 for trans in chain.values())
    return statistics.mean(entropias), deterministicos / len(chain)

def avaliar(corpus, ordem, seed):
    notas, fallbacks, chain = gerar(corpus, ordem, seed)
    entropia, deterministicos = estatisticas_modelo(chain)

    todas_alturas = [n for seq in corpus for n in seq]
    todos_intervalos = [i for seq in corpus for i in intervalos(seq)]

    return {
        "ordem": ordem,
        "seed": seed,
        "mem_4": taxa_memorizacao(notas, corpus, 4),
        "mem_8": taxa_memorizacao(notas, corpus, 8),
        "maior_trecho": maior_trecho_copiado(notas, corpus),
        "dist_altura": distancia(notas, todas_alturas),
        "dist_intervalo": distancia(intervalos(notas), todos_intervalos),
        "fallbacks": fallbacks,
        "entropia": entropia,
        "deterministicos": deterministicos,
    }

def imprimir_tabela(linhas):
    print(f"\nMédias de {len(SEEDS)} seeds por ordem\n")
    print("ordem  " + "  ".join(f"{c:>15}" for c in CAMPOS))

    for ordem in ORDENS:
        grupo = [l for l in linhas if l["ordem"] == ordem]
        medias = "  ".join(
            f"{statistics.mean(l[c] for l in grupo):15.2f}" for c in CAMPOS
        )
        print(f"{ordem:5}  {medias}")

def salvar_csv(linhas, caminho="resultados_avaliacao.csv"):
    with open(caminho, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas[0]))
        writer.writeheader()
        writer.writerows(linhas)
    print(f"\nResultados por seed salvos em {caminho}")

def main():
    corpus = CorpusReader("corpus").read_corpus()

    linhas = []
    for ordem in ORDENS:
        for seed in SEEDS:
            linhas.append(avaliar(corpus, ordem, seed))

    imprimir_tabela(linhas)
    salvar_csv(linhas)

if __name__ == "__main__":
    main()