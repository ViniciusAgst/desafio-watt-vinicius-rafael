# Desafio Watt — Simulador Industrial + Middleware

Simulação de uma planta industrial (rede elétrica, compressor de ar e extrusora) que publica dados via **MQTT**, é consumida por um **middleware** que grava os dados em **PostgreSQL** (com buffer local em **SQLite** para quando o banco cai) e expõe tudo via um servidor **OPC UA**. O simulador também possui um **dashboard web** (Flask) para acompanhar e forçar falhas nos ativos.

## Arquitetura

```text
simulator/  → gera os dados dos ativos (Grid, AirCompressor, Extruder)
              e publica em tópicos MQTT (simulator/grid, .../aircompressor, .../extruder)
              + expõe um dashboard web em http://localhost:5000

middleware/ → assina os tópicos MQTT, guarda os dados em cache (memória),
              persiste no PostgreSQL (ou no buffer SQLite se o Postgres
              estiver fora do ar) e expõe tudo via servidor OPC UA

supervisorio/ → projeto Elipse E3 responsável pela visualização dos dados
                através do servidor OPC UA
```

Fluxo de dados:

```text
simulator (MQTT publisher)
        ↓
broker MQTT
        ↓
middleware (MQTT subscriber)
        ↓
cache em memória
        ↓
PostgreSQL
(ou buffer SQLite se offline)
        ↓
servidor OPC UA
        ↓
Elipse E3 / SCADA
```

## Pré-requisitos

Além do Python, o projeto depende dos seguintes componentes:

* **Python 3.10+**
* **Elipse E3**
* **Broker MQTT** (ex: Mosquitto) escutando em `localhost:1883`
* **PostgreSQL** escutando em `localhost:5432`
* Banco PostgreSQL chamado `simulador`
* Usuário PostgreSQL `postgres`
* Senha PostgreSQL `root`

### Instalando o Mosquitto

**Windows:** baixe o instalador no site oficial do Mosquitto.

**Linux (Debian/Ubuntu):**

```bash
sudo apt install mosquitto mosquitto-clients
```

**macOS:**

```bash
brew install mosquitto
```

Depois de instalado, garanta que o serviço esteja rodando. Por padrão, o Mosquitto utiliza a porta `1883`.

### Criando o banco no PostgreSQL

Com o PostgreSQL instalado e rodando, crie o banco `simulador`:

```bash
psql -U postgres -c "CREATE DATABASE simulador;"
```

> As tabelas (`ativos` e `medicoes`) são criadas automaticamente pelo próprio middleware na primeira conexão. Não é necessário executar nenhum script de schema.

Se sua senha, usuário ou porta do PostgreSQL forem diferentes de `postgres`/`root`, ajuste as configurações em `middleware/main.py`.

> Caso o PostgreSQL esteja indisponível no momento em que o middleware iniciar, os dados serão gravados automaticamente em um buffer local (`buffer.db`, SQLite) e sincronizados assim que o banco voltar a responder.

## Instalação

### 1. Clone o repositório

```powershell
git clone https://github.com/ViniciusAgst/desafio-watt-vinicius-rafael.git
cd .\desafio-watt-vinicius-rafael\
```

### 2. Crie um ambiente virtual

Recomendado:

```bash
python -m venv venv
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

**Windows:**

```bash
source venv\Scripts\activate
```

```powershell
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## Como executar

A ordem recomendada para executar o projeto é:

```text
1. Mosquitto
2. PostgreSQL
3. Simulador
4. Middleware
5. Elipse E3
```

### 1. Simulador

É necessário estar dentro da pasta `simulator`. Caso esteja na pasta raiz do projeto:

```powershell
cd simulator
python main.py
```

O simulador:

* Publica dados a cada 1 segundo nos tópicos MQTT:

  * `simulator/grid`
  * `simulator/aircompressor`
  * `simulator/extruder`
* Executa a simulação dos ativos industriais.
* Disponibiliza o dashboard web em:

```text
http://localhost:5000
```

O dashboard possui controles para acompanhar os ativos e forçar/parar falhas.

### 2. Middleware

Abra outro terminal e, a partir da pasta raiz do projeto:

```powershell
cd middleware
$env:PYTHONPATH = ".."
python main.py
```

```bash
cd middleware
export PYTHONPATH=".."
python main.py
```

O middleware:

* Conecta ao broker MQTT.
* Assina os tópicos publicados pelo simulador.
* Mantém os dados em cache.
* Persiste os dados no PostgreSQL.
* Utiliza o `buffer.db` como fallback caso o PostgreSQL esteja indisponível.
* Sincroniza os dados armazenados no buffer quando o PostgreSQL voltar.
* Inicializa o servidor OPC UA em:

```text
opc.tcp://localhost:4840
```

O servidor OPC UA pode ser acessado por clientes OPC UA, como o Elipse E3 ou UaExpert.

### 3. Elipse E3 — Supervisório

Após iniciar o **middleware** e confirmar que o servidor OPC UA está disponível em:

```text
opc.tcp://localhost:4840
```

é necessário configurar e executar o supervisório desenvolvido no **Elipse E3**.

#### Extraindo o supervisório

Na raiz do projeto existe o arquivo:

```text
supervisorio.zip
```

Extraia/mantenha essa pasta no computador e abra o arquivo de domínio do Elipse E3 (`.dom`) presente nela.

O arquivo `.dom` é o arquivo de domínio do projeto e deve ser aberto utilizando o **Elipse E3 Studio**.

#### Executando o supervisório

1. Abra o **Elipse E3 Studio**.
2. Abra o arquivo `.dom` localizado na pasta `supervisorio`.
3. Execute o domínio/projeto.
4. Caso seja solicitado login, utilize as credenciais padrão:

```text
Usuário: admin
Senha:   adm
```

O supervisório realiza a comunicação com o servidor OPC UA do middleware para apresentar os dados dos ativos industriais.

> O middleware deve estar em execução antes de iniciar o supervisório para que as tags OPC UA possam fornecer os dados simulados.

### Ordem completa de execução

Em condições normais, abra os componentes nesta ordem:

```text
┌──────────────────────────┐
│       Mosquitto          │
│       MQTT :1883         │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│      PostgreSQL          │
│       :5432              │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│       Simulator          │
│      MQTT Publisher      │
│      Flask :5000         │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│       Middleware         │
│      MQTT Subscriber     │
│      OPC UA :4840        │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│       Elipse E3          │
│       Supervisório       │
└──────────────────────────┘
```

## Estrutura de pastas

```text
desafio-watt-vinicius-rafael-main/
├── middleware/
│   ├── main.py
│   ├── logger.py
│   ├── connection/
│   │   └── mqttclient.py
│   ├── opc/
│   │   └── server.py
│   └── storage/
│       ├── cache.py
│       ├── buffer.py
│       ├── postgres.py
│       └── storagemanager.py
│
├── simulator/
│   ├── main.py
│   ├── logger.py
│   ├── dashboard.py
│   ├── connection/
│   │   └── mqttclient.py
│   ├── assets/
│   │   ├── device.py
│   │   └── devices/
│   ├── templates/
│   │   └── index.html
│   └── static/
│
├── supervisorio.dom
├── banco de dados.sql
│
└── requirements.txt
```

## Solução de problemas

### `ModuleNotFoundError: No module named 'assets'`

Confirme que o simulador está sendo executado de dentro da pasta `simulator`:

```powershell
cd simulator
python main.py
```

### Middleware não conecta ao PostgreSQL

Verifique:

* Se o PostgreSQL está em execução.
* Se o banco `simulador` existe.
* Se usuário e senha estão corretos.
* Se a porta está configurada corretamente em `middleware/main.py`.

Enquanto o PostgreSQL estiver indisponível, o middleware continuará armazenando os dados no `buffer.db`.

### Nada aparece no dashboard

Verifique se o Mosquitto está rodando na porta `1883` antes de iniciar o simulador.

### Elipse E3 não apresenta os dados

Verifique:

1. Se o middleware está em execução.
2. Se o servidor OPC UA está disponível em:

```text
opc.tcp://localhost:4840
```

3. Se o projeto correto foi aberto no Elipse E3.
4. Se o domínio (`.dom`) foi executado.
5. Se o usuário utilizado é:

```text
admin
```

e a senha:

```text
adm
```

6. Se o simulador está em execução e publicando dados via MQTT.

### `DeprecationWarning` sobre `Callback API version 1`

Esse aviso é esperado e inofensivo. A biblioteca `paho-mqtt` mantém compatibilidade com código desenvolvido utilizando a API antiga.
