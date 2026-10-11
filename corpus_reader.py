from pathlib import Path
from music21 import converter, note, chord


class CorpusReader:
    """Lê arquivos MIDI e extrai sequências monofônicas de alturas."""

    def __init__(
        self,
        pasta="corpus",
        minimo_notas=30,
        minimo_alturas=5,
        registro_minimo=60,
    ):
        self.pasta = Path(pasta)
        self.minimo_notas = minimo_notas
        self.minimo_alturas = minimo_alturas
        self.registro_minimo = registro_minimo

    def carregar_corpus(self):
        if not self.pasta.exists():
            raise FileNotFoundError(
                f"A pasta '{self.pasta}' não existe."
            )

        arquivos = sorted(
            list(self.pasta.glob("*.mid"))
            + list(self.pasta.glob("*.midi"))
        )

        if not arquivos:
            raise FileNotFoundError(
                f"Nenhum MIDI encontrado em '{self.pasta}'."
            )

        sequencias = []
        vistas = set()
        descartados = 0

        for arquivo in arquivos:
            try:
                score = converter.parse(str(arquivo))
                eventos = []

                # Os offsets são medidos em tempos musicais.
                for elemento in score.flatten().notes:
                    inicio = float(elemento.offset)

                    if isinstance(elemento, note.Note):
                        altura = elemento.pitch.midi
                    elif isinstance(elemento, chord.Chord):
                        altura = max(
                            p.midi for p in elemento.pitches
                        )
                    else:
                        continue

                    eventos.append((inicio, altura))

                por_inicio = {}

                for inicio, altura in eventos:
                    chave = round(inicio, 4)
                    por_inicio[chave] = max(
                        altura,
                        por_inicio.get(chave, altura),
                    )

                sequencia = [
                    altura
                    for _, altura in sorted(por_inicio.items())
                ]

                if len(sequencia) < self.minimo_notas:
                    descartados += 1
                    print(
                        f"[filtro] {arquivo.name}: poucas notas "
                        f"({len(sequencia)})."
                    )
                    continue

                if len(set(sequencia)) < self.minimo_alturas:
                    descartados += 1
                    print(
                        f"[filtro] {arquivo.name}: poucas alturas distintas."
                    )
                    continue

                if (
                    self.registro_minimo is not None
                    and sum(sequencia) / len(sequencia)
                    < self.registro_minimo
                ):
                    descartados += 1
                    print(
                        f"[filtro] {arquivo.name}: registro médio baixo."
                    )
                    continue

                chave = tuple(sequencia)

                if chave in vistas:
                    descartados += 1
                    print(
                        f"[filtro] {arquivo.name}: sequência duplicada."
                    )
                    continue

                vistas.add(chave)
                sequencias.append(sequencia)

                print(
                    f"[ok] {arquivo.name}: {len(sequencia)} notas, "
                    f"{len(set(sequencia))} alturas distintas."
                )

            except Exception as erro:
                descartados += 1
                print(
                    f"[aviso] Não foi possível ler {arquivo.name}: {erro}"
                )

        if not sequencias:
            raise ValueError(
                "Nenhuma sequência adequada foi encontrada. "
                "Confira os MIDI ou ajuste os filtros."
            )

        total_notas = sum(len(seq) for seq in sequencias)
        total_alturas = len({
            altura
            for seq in sequencias
            for altura in seq
        })

        print("\nResumo do corpus")
        print(f"Arquivos encontrados: {len(arquivos)}")
        print(f"Sequências aproveitadas: {len(sequencias)}")
        print(f"Arquivos ou sequências descartados: {descartados}")
        print(f"Total de notas: {total_notas}")
        print(f"Alturas MIDI distintas: {total_alturas}")

        return sequencias