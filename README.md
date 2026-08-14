# Desafio Watt — Simulador Industrial + Middleware

Simulação de uma planta industrial (rede elétrica, compressor de ar e extrusora)
que publica dados via **MQTT**, é consumida por um **middleware** que grava os
dados em **PostgreSQL** (com buffer local em **SQLite** para quando o banco cai)
e expõe tudo via um servidor **OPC UA**. O simulador também tem um **dashboard
web** (Flask) para acompanhar e forçar falhas nos ativos.

## Arquitetura

```
simulator/  → gera os dados dos ativos (Grid, AirCompressor, Extruder)
              e publica em tópicos MQTT (simulator/grid, .../aircompressor, .../extruder)
              + expõe um dashboard web em http://localhost:5000

middleware/ → assina os tópicos MQTT, guarda os dados em cache (memória),
              persiste no PostgreSQL (ou no buffer SQLite se o Postgres
              estiver fora do ar) e expõe tudo via servidor OPC UA
              em opc.tcp://localhost:4840
```

Fluxo de dados:

```
simulator (MQTT publisher) → broker MQTT → middleware (MQTT subscriber)
    → cache em memória → PostgreSQL (ou buffer SQLite se offline)
    → servidor OPC UA (para SCADA/Elipse, etc.)
```

## Pré-requisitos

Além do Python, o projeto depende de dois serviços externos rodando localmente:

- **Python 3.10+**
- **Elipse E3**
- **Broker MQTT** (ex: [Mosquitto](https://mosquitto.org/download/)) escutando em `localhost:1883`
- **PostgreSQL** escutando em `localhost:5432`, com um banco chamado `simulador`
  (usuário `postgres`, senha `root` — configurado em `middleware/main.py`)

### Instalando o Mosquitto

- **Windows**: baixe o instalador em https://mosquitto.org/download/
- **Linux (Debian/Ubuntu)**: `sudo apt install mosquitto mosquitto-clients`
- **macOS**: `brew install mosquitto`

Depois de instalado, garanta que o serviço está rodando (por padrão já sobe na porta 1883).

### Criando o banco no PostgreSQL

Com o PostgreSQL instalado e rodando, crie o banco `simulador`:

```bash
psql -U postgres -c "CREATE DATABASE simulador;"
```

> As tabelas (`ativos` e `medicoes`) são criadas automaticamente pelo próprio
> middleware na primeira conexão — não precisa rodar nenhum script de schema.

Se sua senha/usuário do Postgres forem diferentes de `postgres`/`root`, ajuste
nas configurações em `middleware/main.py`.

> Caso o Postgres esteja indisponível no momento em que o middleware iniciar,
> os dados são gravados automaticamente em um buffer local (`buffer.db`,
> SQLite) e sincronizados assim que o banco voltar a responder — não é
> necessário nenhum passo extra para isso.

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/ViniciusAgst/desafio-watt-vinicius-rafael.git
   cd .\desafio-watt-vinicius-rafael\
   ```

2. (Recomendado) Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Como executar

Certifique-se de que o **Mosquitto** e o **PostgreSQL** já estão rodando antes
de iniciar as aplicações abaixo. Abra dois terminais (um para cada parte).

### 1. Simulador (gera os dados e sobe o dashboard)

É necessário esta dentro da pasta do simulador, caso esteja na paste raiz do projeto:

```powershell
cd simulator
python main.py          
```

- Publica dados a cada 1s nos tópicos MQTT `simulator/grid`, `simulator/aircompressor` e `simulator/extruder`.
- Dashboard web disponível em **http://localhost:5000**, com botões para forçar/parar falha em cada ativo.

### 2. Middleware (consome, persiste e expõe via OPC UA)

É necessário esta dentro da pasta do middleware, caso esteja na paste raiz do projeto:

```bash
cd middleware
$env:PYTHONPATH = ".."
python main.py
```

- Conecta ao broker MQTT e assina os tópicos publicados pelo simulador.
- Grava os dados no PostgreSQL (com fallback para buffer SQLite).
- Sobe um servidor OPC UA em **opc.tcp://localhost:4840** (pode ser lido por qualquer cliente/SCADA OPC UA, ex: UaExpert).

> A ordem recomendada é: Mosquitto/Postgres → simulador → middleware (o
> middleware só passa a ter dados assim que o simulador começar a publicar).

## Estrutura de pastas

```
desafio-watt-vinicius-rafael-main/
├── middleware/
│   ├── main.py                    # ponto de entrada do middleware
│   ├── logger.py                  # logging simples (info/warn/error/debug), usado por middleware e simulator
│   ├── connection   
│   │   └── mqttclient.py          # assinante MQTT
│   ├── opc   
│   │   └── server.py              # servidor OPC UA
│   └── storage/
│       ├── cache.py               # cache em memória (fila por ativo)
│       ├── buffer.py              # buffer local em SQLite (fallback)
│       ├── postgres.py            # persistência em PostgreSQL
│       └── storagemanager.py      # orquestra cache + postgres + buffer
├── simulator/
│   ├── main.py                    # ponto de entrada do simulador
│   ├── logger.py                  # logging simples (info/warn/error/debug), usado por middleware e simulator
│   ├── dashboard.py                # dashboard Flask
│   ├── connection   
│   │   └── mqttclient.py          # publicador MQTT
│   ├── assets/
│   │   ├── device.py               # classe base + enum de estados
│   │   └── devices/                # Grid, AirCompressor, Extruder
│   ├── templates/index.html
│   └── static/                     # CSS e JS do dashboard
└── requirements.txt
```

## Solução de problemas

- **`ModuleNotFoundError: No module named 'assets'` (ou `connection`,
  `dashboard`) ao rodar o simulador**: confirme que está rodando de **dentro
  da pasta `simulator/`** (esses imports são relativos a ela).
- **Middleware não conecta ao Postgres**: verifique se o serviço está no ar
  e se usuário/senha/porta em `middleware/main.py` batem com sua instalação.
  Enquanto isso, os dados continuam sendo gravados no `buffer.db` local.
- **Nada aparece no dashboard**: confira se o Mosquitto está rodando na porta
  1883 antes de iniciar o simulador.
- Um aviso de `DeprecationWarning` sobre `Callback API version 1` ao rodar o
  middleware é esperado e inofensivo (biblioteca `paho-mqtt` mantendo
  compatibilidade com código escrito para a API antiga).
