
import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from corpus_reader import CorpusReader
from markov_chain import MarkovChain


ORDENS = [1, 2, 3]
SEEDS = range(100, 110)
NUM_NOTAS = 256

CAMPOS = [
    "mem_4",
    "mem_8",
    "maior_trecho",
    "dist_altura",
    "dist_intervalo",
    "fallbacks",
    "entropia",
    "deterministicos",
]


def ngramas(sequencia, n):
    return [
        tuple(sequencia[i:i + n])
        for i in range(len(sequencia) - n + 1)
    ]


def taxa_memorizacao(gerado, corpus, n):
    """Fração de n-gramas gerados encontrados no corpus."""
    conhecidos = set()

    for sequencia in corpus:
        conhecidos.update(ngramas(sequencia, n))

    gerados = ngramas(gerado, n)

    if not gerados:
        return 0.0

    encontrados = sum(
        grupo in conhecidos
        for grupo in gerados
    )

    return encontrados / len(gerados)


def trecho_comum(gerado, sequencia):
    """Maior trecho consecutivo compartilhado entre duas sequências."""
    posicoes = defaultdict(list)

    for indice, nota in enumerate(sequencia):
        posicoes[nota].append(indice)

    melhor = 0
    anterior = {}

    for nota in gerado:
        atual = {}

        for indice in posicoes[nota]:
            atual[indice] = anterior.get(indice - 1, 0) + 1

        melhor = max(
            melhor,
            max(atual.values(), default=0),
        )
        anterior = atual

    return melhor


def maior_trecho_copiado(gerado, corpus):
    if not corpus:
        return 0

    return max(
        trecho_comum(gerado, sequencia)
        for sequencia in corpus
    )


def intervalos(sequencia):
    return [
        b - a
        for a, b in zip(sequencia, sequencia[1:])
    ]


def distancia_distribuicoes(a, b):
    """Distância de variação total entre duas distribuições."""
    if not a or not b:
        return 0.0

    ca = Counter(a)
    cb = Counter(b)
    soma = 0.0

    for elemento in set(ca) | set(cb):
        pa = ca[elemento] / len(a)
        pb = cb[elemento] / len(b)
        soma += abs(pa - pb)

    return 0.5 * soma


def avaliar(corpus, ordem, seed):
    modelo = MarkovChain(ordem=ordem, seed=seed)
    modelo.treinar(corpus)

    notas, fallbacks = modelo.gerar_com_estatisticas(
        n_notas=NUM_NOTAS,
        temperatura=1.0,
        evitar_repeticao=True,
    )

    todas_alturas = [
        nota
        for sequencia in corpus
        for nota in sequencia
    ]

    todos_intervalos = [
        intervalo
        for sequencia in corpus
        for intervalo in intervalos(sequencia)
    ]

    return {
        "ordem": ordem,
        "seed": seed,
        "mem_4": taxa_memorizacao(notas, corpus, 4),
        "mem_8": taxa_memorizacao(notas, corpus, 8),
        "maior_trecho": maior_trecho_copiado(notas, corpus),
        "dist_altura": distancia_distribuicoes(
            notas, todas_alturas
        ),
        "dist_intervalo": distancia_distribuicoes(
            intervalos(notas), todos_intervalos
        ),
        "fallbacks": fallbacks,
        "entropia": modelo.entropia_media(),
        "deterministicos": (
            modelo.proporcao_contextos_deterministicos()
        ),
        "notas_distintas": len(set(notas)),
    }


def imprimir_tabela(linhas):
    campos = CAMPOS + ["notas_distintas"]

    print(f"\nMédias por ordem, com {len(SEEDS)} sementes\n")
    print(
        f"{'ordem':>5}  "
        + "  ".join(f"{campo:>16}" for campo in campos)
    )

    for ordem in ORDENS:
        grupo = [
            linha for linha in linhas
            if linha["ordem"] == ordem
        ]

        if not grupo:
            continue

        medias = [
            f"{statistics.mean(linha[c] for linha in grupo):16.3f}"
            for c in campos
        ]

        print(f"{ordem:5}  " + "  ".join(medias))


def salvar_csv(linhas, caminho):
    if not linhas:
        print("Nenhum resultado para salvar.")
        return

    with open(
        caminho,
        "w",
        newline="",
        encoding="utf-8",
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=list(linhas[0].keys()),
        )
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"\nResultados individuais salvos em: {caminho}")


def main():
    corpus = CorpusReader("corpus").carregar_corpus()
    linhas = []

    for ordem in ORDENS:
        for seed in SEEDS:
            print(f"Avaliando ordem={ordem}, seed={seed}...")

            linhas.append(
                avaliar(corpus, ordem, seed)
            )

    imprimir_tabela(linhas)

    caminho = Path("resultados_avaliacao.csv")
    salvar_csv(linhas, caminho)


if __name__ == "__main__":
    main()
