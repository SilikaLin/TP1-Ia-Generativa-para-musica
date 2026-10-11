from collections import Counter, defaultdict
import math
import random

class MarkovChain:
    # Modelo de Markov para gerar melodias a partir de um corpus.

    def __init__(self, ordem=2, seed=None):
        if ordem < 1:
            raise ValueError("A ordem precisa ser >= 1.")

        self.ordem = ordem
        self.rng = random.Random(seed)
        self.transicoes = defaultdict(Counter)
        self.contextos = []
        self.notas_corpus = []

    def treinar(self, sequencias):
        # Conta as transições observadas em cada sequência.
        self.transicoes.clear()
        self.contextos.clear()
        self.notas_corpus = []

        for sequencia in sequencias:
            notas = [int(nota) for nota in sequencia]

            if len(notas) <= self.ordem:
                continue

            self.notas_corpus.extend(notas)

            for i in range(len(notas) - self.ordem):
                contexto = tuple(notas[i:i + self.ordem])
                proxima = notas[i + self.ordem]
                self.transicoes[contexto][proxima] += 1

        self.contextos = sorted(self.transicoes.keys())

        if not self.contextos:
            raise ValueError(
                "Não há sequências suficientes para treinar o modelo."
            )

        print(
            f"Modelo treinado: ordem={self.ordem}, "
            f"contextos={len(self.contextos)}, "
            f"notas observadas={len(self.notas_corpus)}."
        )

    def _escolher_ponderado(self, pesos):
        # Escolhe uma nota proporcionalmente ao seu peso.
        itens = list(pesos.items())
        total = sum(peso for _, peso in itens)

        if total <= 0:
            raise ValueError("Os pesos precisam ser positivos.")

        alvo = self.rng.random() * total
        acumulado = 0.0

        for item, peso in itens:
            acumulado += peso
            if alvo < acumulado:
                return item

        return itens[-1][0]

    def _gerar(
        self,
        n_notas,
        temperatura,
        evitar_repeticao=True,
    ):
        if not self.contextos:
            raise RuntimeError("Execute treinar() antes de gerar música.")

        if n_notas < 1:
            raise ValueError("A quantidade de notas precisa ser positiva.")

        if temperatura <= 0:
            raise ValueError("A temperatura precisa ser maior que zero.")

        contexto = self.rng.choice(self.contextos)
        resultado = list(contexto)
        fallbacks = 0

        while len(resultado) < n_notas:
            contexto_atual = tuple(resultado[-self.ordem:])
            opcoes = self.transicoes.get(contexto_atual)

            if not opcoes:
                # Reinicia a partir de um contexto observado no corpus.
                fallbacks += 1
                novo_contexto = self.rng.choice(self.contextos)
                resultado.extend(novo_contexto)
                continue

            pesos = {}

            for nota, frequencia in opcoes.items():
                peso = frequencia ** (1.0 / temperatura)

                # Reduz, mas não proíbe, três notas iguais consecutivas.
                if (
                    evitar_repeticao
                    and len(resultado) >= 2
                    and nota == resultado[-1] == resultado[-2]
                ):
                    peso *= 0.25

                pesos[nota] = peso

            resultado.append(self._escolher_ponderado(pesos))

        return resultado[:n_notas], fallbacks

    def gerar(
        self,
        n_notas=256,
        temperatura=1.0,
        evitar_repeticao=True,
    ):
        # Gera uma sequência de alturas MIDI.
        notas, _ = self._gerar(
            n_notas,
            temperatura,
            evitar_repeticao,
        )
        return notas

    def gerar_com_estatisticas(
        self,
        n_notas=256,
        temperatura=1.0,
        evitar_repeticao=True,
    ):
        # Gera notas e informa quantos fallbacks ocorreram.
        return self._gerar(
            n_notas,
            temperatura,
            evitar_repeticao,
        )

    def probabilidades(self, contexto):
        # Retorna as probabilidades aprendidas para um contexto.
        contexto = tuple(contexto)
        contagens = self.transicoes.get(contexto)

        if not contagens:
            return {}

        total = sum(contagens.values())

        return {
            nota: quantidade / total
            for nota, quantidade in sorted(contagens.items())
        }

    def entropia_media(self):
        # Calcula a entropia média das distribuições de transição.
        if not self.transicoes:
            return 0.0

        entropias = []

        for contagens in self.transicoes.values():
            total = sum(contagens.values())
            entropia = 0.0

            for quantidade in contagens.values():
                p = quantidade / total
                entropia -= p * math.log2(p)

            entropias.append(entropia)

        return sum(entropias) / len(entropias)

    def proporcao_contextos_deterministicos(self):
        # Proporção de contextos com apenas uma próxima nota possível.
        if not self.transicoes:
            return 0.0

        deterministas = sum(
            len(contagens) == 1
            for contagens in self.transicoes.values()
        )

        return deterministas / len(self.transicoes)

    def get_numero_contextos(self):
        return len(self.contextos)