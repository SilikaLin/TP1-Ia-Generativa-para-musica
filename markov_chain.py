import random
from collections import defaultdict

def _como_sequencias(corpus):
    # se vier uma sequência só, embrulha numa lista
    if corpus and not isinstance(corpus[0], (list, tuple)):
        return [corpus]
    return corpus

class MarkovChain:

    def __init__(self, seed, current_state, order=1):
        self.rand = random.Random(seed)
        self.current_state = current_state
        self.order = order

        # contexto (tupla de notas) -> {próxima nota: probabilidade}
        self.chain = {}
        self.history = []
        self.states = []

        # quantas vezes o step() caiu num contexto que não existe
        self.fallbacks = 0

    def train(self, corpus):
        sequencias = []
        for seq in _como_sequencias(corpus):
            if len(seq) > self.order:
                sequencias.append(seq)

        if not sequencias:
            raise ValueError("Corpus pequeno demais para essa ordem")

        notas = set()
        for seq in sequencias:
            notas.update(seq)
        self.states = sorted(notas)

        # cada sequência é contada separada, pra não criar transição
        # falsa do fim de uma voz pro começo da outra
        counts = defaultdict(lambda: defaultdict(int))
        for seq in sequencias:
            for i in range(len(seq) - self.order):
                context = tuple(seq[i:i + self.order])
                counts[context][seq[i + self.order]] += 1

        # ordenei pra mesma seed dar sempre o mesmo resultado
        self.chain = {}
        for context in sorted(counts):
            total = sum(counts[context].values())
            self.chain[context] = {
                note: n / total
                for note, n in sorted(counts[context].items())
            }

        self.history = []
        print(
            f"Cadeia treinada: ordem {self.order}, "
            f"{len(self.states)} estados, {len(self.chain)} contextos"
        )

    def set_initial_state(self, corpus):
        sequencias = []
        for seq in _como_sequencias(corpus):
            if len(seq) >= self.order:
                sequencias.append(seq)

        if not sequencias:
            raise ValueError("Poucas notas para iniciar a cadeia")

        total_posicoes = 0
        for seq in sequencias:
            total_posicoes += len(seq) - self.order + 1

        # sorteia uma posição qualquer, em qualquer sequência
        sorteio = self.rand.randrange(total_posicoes)

        for seq in sequencias:
            posicoes = len(seq) - self.order + 1
            if sorteio < posicoes:
                self.history = list(seq[sorteio:sorteio + self.order])
                break
            sorteio -= posicoes

        self.current_state = self.history[-1]

    def step(self):
        if not self.chain:
            raise RuntimeError("Chame train() antes de gerar notas")

        context = tuple(self.history[-self.order:])

        # contexto que não existe (tipo a última nota de uma voz):
        # pega outro qualquer e continua dali
        if context not in self.chain:
            self.fallbacks += 1
            context = self.rand.choice(list(self.chain))
            self.history = list(context)

        transitions = self.chain[context]
        next_note = self.rand.choices(
            list(transitions),
            weights=list(transitions.values()),
        )[0]

        self.current_state = next_note
        self.history = (self.history + [next_note])[-self.order:]
        return next_note

    def gerar(self, corpus, n_notas):
        self.set_initial_state(corpus)
        self.fallbacks = 0

        notas = list(self.history)
        while len(notas) < n_notas:
            notas.append(self.step())
        return notas

    def print_transition_matrix(self):
        # só dá pra mostrar como matriz quadrada na ordem 1
        if self.order != 1:
            print("Matriz disponível só para ordem 1")
            return

        print("\nMATRIZ DE TRANSIÇÃO\n")
        print("      " + " ".join(f"{s:6}" for s in self.states))

        for a in self.states:
            row = self.chain.get((a,), {})
            values = " ".join(f"{row.get(b, 0):6.2f}" for b in self.states)
            print(f"{a:4}  {values}")

    def get_current_state(self):
        return self.current_state

    def get_order(self):
        return self.order

    def get_number_of_contexts(self):
        return len(self.chain)