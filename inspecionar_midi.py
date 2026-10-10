import argparse
import struct
from leitor_midi import ler_midi, extrair_notas

NOMES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

EVENTOS_META = {
    0x00: "sequence_number", 0x01: "text", 0x02: "copyright",
    0x03: "track_name", 0x04: "instrument_name", 0x05: "lyric",
    0x06: "marker", 0x07: "cue_point", 0x20: "channel_prefix",
    0x2F: "end_of_track", 0x51: "set_tempo", 0x54: "smpte_offset",
    0x58: "time_signature", 0x59: "key_signature", 0x7F: "sequencer_specific",
}

def nome_nota(numero):
    return f"{NOMES_NOTAS[numero % 12]}{numero // 12 - 1}"

def mapa_de_tempo(trilhas):
    # lista ordenada de (tick, microssegundos por semínima)
    mapa = []
    for trilha in trilhas:
        for ev in trilha:
            if ev["tipo"] == "meta" and ev["meta"] == 0x51:
                mapa.append((ev["tick"], int.from_bytes(ev["dados"], "big")))
    return sorted(mapa)

def para_segundos(tick, divisao, mapa):
    segundos = 0.0
    tick_anterior, us = 0, 500000  # padrão do MIDI: 120 bpm

    for tick_mudanca, novo_us in mapa:
        if tick_mudanca >= tick:
            break
        segundos += (tick_mudanca - tick_anterior) * us / divisao / 1e6
        tick_anterior, us = tick_mudanca, novo_us

    return segundos + (tick - tick_anterior) * us / divisao / 1e6

def descrever_meta(tipo, conteudo):
    nome = EVENTOS_META.get(tipo, f"meta_0x{tipo:02X}")

    if tipo == 0x51:
        us = int.from_bytes(conteudo, "big")
        return f"{nome}: {us} µs/semínima ({60_000_000 / us:.1f} bpm)"
    if tipo == 0x58 and len(conteudo) == 4:
        return f"{nome}: {conteudo[0]}/{2 ** conteudo[1]}"
    if tipo == 0x59 and len(conteudo) == 2:
        acidentes, menor = struct.unpack("bB", conteudo)
        especie = "sustenidos" if acidentes > 0 else "bemóis"
        modo = "menor" if menor else "maior"
        return f"{nome}: {abs(acidentes)} {especie}, {modo}"
    if 0x01 <= tipo <= 0x07:
        return f"{nome}: {conteudo.decode('utf-8', errors='replace')!r}"

    return f"{nome} {conteudo.hex()}".rstrip()

def descrever(ev):
    tipo = ev["tipo"]

    if tipo == "meta":
        return descrever_meta(ev["meta"], ev["dados"])
    if tipo == "sysex":
        return f"sysex ({len(ev['dados'])} bytes)"

    canal, dados = ev["canal"], ev["dados"]

    if tipo in ("note_on", "note_off"):
        nota, velocity = dados
        extra = ""
        if tipo == "note_on" and velocity == 0:
            extra = "  (velocity 0 equivale a note_off)"
        return (
            f"{tipo:<14} canal={canal} nota={nota} ({nome_nota(nota)}) "
            f"velocity={velocity}{extra}"
        )
    if tipo == "program_change":
        return f"{tipo:<14} canal={canal} instrumento={dados[0]}"
    if tipo == "control_change":
        return f"{tipo:<14} canal={canal} controle={dados[0]} valor={dados[1]}"
    if tipo == "pitch_bend":
        return f"{tipo:<14} canal={canal} valor={(dados[0] | (dados[1] << 7)) - 8192}"

    return f"{tipo:<14} canal={canal} dados={dados}"

def imprimir_resumo(caminho, formato, divisao, trilhas, mapa):
    notas = extrair_notas(trilhas)

    print(f"Arquivo: {caminho}")
    print(f"Formato {formato}, {len(trilhas)} trilhas, {divisao} ticks por semínima")

    if mapa:
        bpm = 60_000_000 / mapa[0][1]
        print(f"Andamento: {bpm:.1f} bpm ({len(mapa)} marcação(ões) de tempo)")
    else:
        print("Andamento: 120 bpm (padrão do MIDI, nenhum set_tempo no arquivo)")

    if not notas:
        print("Nenhuma nota encontrada.")
        return

    duracoes = set()
    for ini, fim, _, _ in notas:
        duracao = para_segundos(fim, divisao, mapa) - para_segundos(ini, divisao, mapa)
        duracoes.add(round(duracao * 1000))
    duracoes = sorted(duracoes)

    velocities = sorted({vel for *_, vel in notas})
    alturas = [nota for _, _, nota, _ in notas]
    fim_total = max(fim for _, fim, _, _ in notas)

    print(f"Notas: {len(notas)}, duração total {para_segundos(fim_total, divisao, mapa):.1f} s")
    print(f"Alturas: de {nome_nota(min(alturas))} ({min(alturas)}) a {nome_nota(max(alturas))} ({max(alturas)})")
    print(f"Velocities usadas: {velocities}")

    if len(duracoes) <= 6:
        print(f"Duração das notas: {duracoes} ms")
    else:
        print(f"Duração das notas: de {duracoes[0]} a {duracoes[-1]} ms ({len(duracoes)} valores)")

def main():
    parser = argparse.ArgumentParser(description="Mostra os eventos de um arquivo MIDI.")
    parser.add_argument("arquivo")
    parser.add_argument("--max", type=int, default=40, help="eventos por trilha (padrão: 40)")
    parser.add_argument("--tudo", action="store_true", help="mostra todos os eventos")
    args = parser.parse_args()

    formato, divisao, trilhas = ler_midi(args.arquivo)
    mapa = mapa_de_tempo(trilhas)

    imprimir_resumo(args.arquivo, formato, divisao, trilhas, mapa)

    limite = None if args.tudo else args.max

    for i, trilha in enumerate(trilhas):
        print(f"\n--- Trilha {i}: {len(trilha)} eventos ---")
        print(f"{'tick':>8}  {'tempo':>9}  evento")

        for ev in trilha[:limite]:
            segundos = para_segundos(ev["tick"], divisao, mapa)
            print(f"{ev['tick']:8}  {segundos:8.3f}s  {descrever(ev)}")

        if limite is not None and len(trilha) > limite:
            print(f"... mais {len(trilha) - limite} eventos (use --max N ou --tudo)")

if __name__ == "__main__":
    main()