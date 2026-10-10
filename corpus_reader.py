import statistics
import struct
from collections import defaultdict
from pathlib import Path
from leitor_midi import ler_midi, extrair_notas

CANAL_BATERIA = 9  # canal 10 do General MIDI (percussão)

class CorpusReader:

    MIN_NOTAS = 30    # menos que isso é efeito sonoro ou enfeite
    MIN_ALTURAS = 5   # menos que isso é basicamente uma nota repetida

    def __init__(self, corpus_folder="corpus", registro_minimo=60):
        self.corpus_folder = Path(corpus_folder)
        self.registro_minimo = registro_minimo

    def get_midi_files(self):
        if not self.corpus_folder.exists():
            raise FileNotFoundError(f"A pasta '{self.corpus_folder}' não existe.")

        files = list(self.corpus_folder.glob("*.mid"))
        files += self.corpus_folder.glob("*.midi")
        return sorted(files)

    def linha_mais_aguda(self, notas):
        # acorde (várias notas no mesmo início): fica só a mais aguda
        mais_aguda = {}
        for inicio, _, altura, _ in notas:
            mais_aguda[inicio] = max(altura, mais_aguda.get(inicio, 0))
        return [mais_aguda[inicio] for inicio in sorted(mais_aguda)]

    def voz_serve(self, sequencia):
        if len(sequencia) < self.MIN_NOTAS:
            return False
        if len(set(sequencia)) < self.MIN_ALTURAS:
            return False
        return statistics.mean(sequencia) >= self.registro_minimo

    def read_file(self, filepath):
        # uma sequência de alturas por voz (trilha + canal), sem a bateria
        _, _, trilhas = ler_midi(filepath)
        sequencias = []

        for trilha in trilhas:
            por_canal = defaultdict(list)
            for ev in trilha:
                if ev["tipo"] in ("note_on", "note_off") and ev["canal"] != CANAL_BATERIA:
                    por_canal[ev["canal"]].append(ev)

            for eventos in por_canal.values():
                sequencia = self.linha_mais_aguda(extrair_notas([eventos]))
                if self.voz_serve(sequencia):
                    sequencias.append(sequencia)

        return sequencias

    def read_corpus(self):
        midi_files = self.get_midi_files()

        if not midi_files:
            raise FileNotFoundError(
                f"Nenhum .mid ou .midi na pasta '{self.corpus_folder}'."
            )

        corpus = []
        vistas = set()  # tem MIDI que dobra a melodia, aí as vozes ficam iguais

        for filepath in midi_files:
            try:
                vozes = self.read_file(filepath)
            except (ValueError, IndexError, KeyError, struct.error) as erro:
                print(f"Ignorando {filepath.name}: {erro!r}")
                continue

            novas = []
            for voz in vozes:
                if tuple(voz) not in vistas:
                    vistas.add(tuple(voz))
                    novas.append(voz)

            print(f"Lendo {filepath.name}: {len(novas)} vozes, {sum(map(len, novas))} notas")
            corpus.extend(novas)

        if not corpus:
            raise ValueError("Nenhuma voz aproveitável nos MIDIs da pasta.")

        print(f"Total no corpus: {len(corpus)} vozes, {sum(map(len, corpus))} notas")
        return corpus