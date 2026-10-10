import struct

EVENTOS_CANAL = {
    0x80: "note_off",
    0x90: "note_on",
    0xA0: "aftertouch",
    0xB0: "control_change",
    0xC0: "program_change",
    0xD0: "channel_pressure",
    0xE0: "pitch_bend",
}

def ler_varlen(dados, pos):
    # número de tamanho variável do MIDI, 7 bits por byte
    valor = 0
    while True:
        byte = dados[pos]
        pos += 1
        valor = (valor << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return valor, pos

def ler_trilha(dados):
    eventos = []
    pos = 0
    tick = 0
    status = None

    while pos < len(dados):
        delta, pos = ler_varlen(dados, pos)
        tick += delta
        byte = dados[pos]

        if byte == 0xFF:  # meta-evento
            tipo = dados[pos + 1]
            tamanho, pos = ler_varlen(dados, pos + 2)
            eventos.append({
                "tick": tick, "tipo": "meta", "meta": tipo,
                "dados": dados[pos:pos + tamanho],
            })
            pos += tamanho

        elif byte in (0xF0, 0xF7):  # sysex
            tamanho, pos = ler_varlen(dados, pos + 1)
            eventos.append({
                "tick": tick, "tipo": "sysex", "dados": dados[pos:pos + tamanho],
            })
            pos += tamanho

        else:
            if byte & 0x80:
                status = byte
                pos += 1
            elif status is None:
                raise ValueError("arquivo MIDI inválido (evento sem status)")
            # sem o bit 80 é running status, vale o status do evento anterior

            tipo = status & 0xF0
            quantidade = 1 if tipo in (0xC0, 0xD0) else 2
            eventos.append({
                "tick": tick, "tipo": EVENTOS_CANAL[tipo], "canal": status & 0x0F,
                "dados": list(dados[pos:pos + quantidade]),
            })
            pos += quantidade
    return eventos

def ler_midi(caminho):
    with open(caminho, "rb") as f:
        dados = f.read()

    if dados[:4] != b"MThd":
        raise ValueError("isso não parece um arquivo MIDI")

    formato, n_trilhas, divisao = struct.unpack(">HHH", dados[8:14])
    if divisao & 0x8000:
        raise ValueError("divisão de tempo SMPTE não é suportada")

    pos = 8 + struct.unpack(">I", dados[4:8])[0]
    trilhas = []
    for _ in range(n_trilhas):
        if dados[pos:pos + 4] != b"MTrk":
            raise ValueError("trilha esperada, mas não encontrada")
        tamanho = struct.unpack(">I", dados[pos + 4:pos + 8])[0]
        pos += 8
        trilhas.append(ler_trilha(dados[pos:pos + tamanho]))
        pos += tamanho

    return formato, divisao, trilhas

def extrair_notas(trilhas):
    # junta cada note_on com o note_off dele: (início, fim, nota, velocity)
    notas = []

    for trilha in trilhas:
        abertas = {}
        for ev in trilha:
            if ev["tipo"] not in ("note_on", "note_off"):
                continue

            nota, velocity = ev["dados"]
            chave = (ev["canal"], nota)

            if ev["tipo"] == "note_on" and velocity > 0:
                abertas[chave] = (ev["tick"], velocity)
            elif chave in abertas:
                inicio, velocity_inicial = abertas.pop(chave)
                notas.append((inicio, ev["tick"], nota, velocity_inicial))

    return notas