## Trabalho Prático 1 -  IA Generativa para Música
#### Geração Musical por Cadeias de Markov

## Sobre

Este projeto é a implementação de um sistema de composição musical algorítmica baseado em Cadeias de Markov. O sistema adota como restrição temática a geração de melodias inspiradas na música de jogos eletrônicos clássicos. O modelo aprende transições entre alturas de notas a partir de arquivos MIDI de músicas de jogos clássicos que estão na pasta corpus e utiliza essas transições para gerar novas melodias. 

A saída principal é um arquivo MIDI. Opcionalmente, o MIDI pode serconvertido para WAV usando FluidSynth e uma SoundFont.

As músicas geradas são salvas nos formatos:
.mid — representação simbólica da música;

Este projeto usa imports da biblioteca padrão de Python:
- argparse
- random
- pathlib
- collections
- statistics
- math
- shutil
- csv

## Requisitos

- Python 3.10 ou superior
- music21
- FluidSynth, para conversão em áudio
- Uma SoundFont no formato `.sf2`, para conversão em áudio
- Arquivos MIDI no diretório `corpus/`

## Como Executar
### Terminal Linux

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências Python:

```bash
python -m pip install -r requirements.txt
```

Em Ubuntu ou Debian, instale o FluidSynth:

```bash
sudo apt update
sudo apt install fluidsynth
```
Coloque os arquivos MIDI em `corpus/`. Para gerar áudio, coloque uma
SoundFont no projeto ou informe seu caminho pelo argumento `--soundfont`.

## Gerar uma música

Somente MIDI:

```bash
python main.py --ordem 2 --perfil aventura --seed 100 --sem-wav
```

MIDI e WAV:

```bash
python main.py --ordem 2 --perfil aventura --seed 100
```

Gerar uma música mais curta:

```bash
python main.py --ordem 2 --notas 128 --seed 200 --sem-wav
```

Gerar sem acompanhamento:

```bash
python main.py --ordem 2 --perfil exploracao --seed 300 \
  --sem-acompanhamento --sem-wav
```

## Perfis disponíveis

- `aventura`
- `suspense`
- `arcade`

Cada perfil define andamento, distribuição de durações e temperatura de geração.

## Avaliação técnica

Execute:

```bash
python avaliacao.py
```
O programa compara as ordens 1, 2 e 3 com dez sementes por ordem.
Os resultados individuais são salvos em `resultados_avaliacao.csv`.

## Reprodutibilidade

Para repetir uma geração, use o mesmo corpus, a mesma ordem, a mesma
semente e os mesmos parâmetros.

Exemplo:

```bash
python main.py --ordem 2 --perfil aventura --seed 100 --sem-wav
```

## Demonstrações em áudio

O sistema gera composições musicais no formato MIDI utilizando cadeias de Markov treinadas com um corpus de músicas de jogos eletrônicos clássicos. Para facilitar a avaliação dos resultados, foram sintetizadas versões em áudio das músicas geradas.

As composições utilizam diferentes perfis musicais e sementes aleatórias, permitindo observar variações entre as execuções.

Os arquivos MIDI permitem reproduzir e analisar as composições simbolicamente, enquanto os arquivos de áudio facilitam a comparação auditiva entre os resultados.

As músicas estao salvas na pasta musicas, com ambos os arquivos .mid e .wav executavel.

## Usos de Ia

Foram utilizadas IA para ajudar em duvidas, e melhorar o texto.

Os prompts:

https://chatgpt.com/s/p_6acbe1ccff688191acbd69dae7e6328c
https://chatgpt.com/s/p_6acbe1e8c7908191ab864b22a78c9058
https://chatgpt.com/s/p_6acbe1fea14c8191a62e717e96821572
https://chatgpt.com/s/p_6acbe21bcddc8191a573a007db184ed2
https://chatgpt.com/s/p_6acbe30b63cc8191bc997d25febfb4e2
https://chatgpt.com/s/p_6acbe3a687a08191ab7ef7026145396e
https://chatgpt.com/s/p_6acbe63fb0d08191b34d38f3c3cd3a02