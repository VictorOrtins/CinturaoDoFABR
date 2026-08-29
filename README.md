# Cinturão do Futebol Americano Brasileiro

## Metodologia

1. **Scraping de todas as partidas que já ocorreram no FABR**: Uso de bibliotecas de web scrapping para raspar dados do site Salão Oval com todas as partidas ocorridas no FABR
   
2. **Computar resultados**: A partir dos dados obtidos, a ideia é computar os resultados e ver quem está com o cinturão do FABR hoje.

3. **Análises relacionadas**: Além disso, serão feitas diversas análises sobre o cinturão, quem mais esteve com sua posse, quem mais desafiou o campeão, em conjunto com outras análises a definir.

4. **Criação de Web App**: Será feito um aplicativo para browsers para mostrar os resultados ao público.

## Estrutura do Projeto

- **`app/`**: Protótipo do aplicativo web utilizando Streamlit (mantido como referência).
- **`backend/`**: API do V1, em FastAPI (uv project) com um banco SQLite temporário,
  sincronizado a partir dos CSVs em `backend/seed_data/` (schema gerenciado via Alembic).
- **`frontend/`**: Aplicativo web do V1, em React + Vite + TypeScript.
- **`scripts/`**: Scripts para subir/derrubar o projeto localmente via Docker.
- **`notebooks/`**: Notebooks Jupyter que documentam análises feitas em cima dos dados obtidos.
- **`src/`**: Contém os scripts Python para coleta de dados e cálculos estatísticos:
  - **`cinturao_algorithm/`**: Scripts do algoritmo do cinturão
  - **`preprocessing/`**: Scripts de pré-processamento dos dados advindos do scraping.
  - **`scraping/`**: Scripts para web scraping de todos os resultados históricos do FABR.
  - **`pipeline/`**: Funções orquestrador-agnósticas (scrape incremental, merge, algoritmo
    do cinturão, sync dos CSVs) usadas tanto pela CLI manual quanto pelo DAG do Airflow.
  - **`utils/`**: Funções em comum para todos os arquivos.
- **`dags/`**: DAG do Airflow (`update_fabr_data`) que orquestra o pipeline acima —
  ver [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md).
- **`data/`**: dados brutos/processados do pipeline (`data/raw/` é parcialmente
  versionado; `data/processed/` é gerado localmente e ignorado pelo git).
- **`.github/workflows/`**: CI — scrape semanal automatizado que abre PR com os dados
  atualizados para revisão (nunca escreve direto em produção).
- **`docs/`**: documentação técnica estendida — [`DATA_PIPELINE.md`](docs/DATA_PIPELINE.md)
  para o pipeline de dados (plano, decisões, status por fase), [`DESIGN.md`](docs/DESIGN.md)
  para a direção visual do frontend.
- **`tests/`**: Contém os testes unitários para o código em `src/` e `dags/`.
- **`README.md`**: Documento explicativo do repositório (você está aqui).
- **`requirements.txt`**: Dependências utilizadas no projeto (scraping/preprocessing/algoritmo).
- **`requirements-airflow.txt`**: Dependência do Airflow — **instalar separadamente**
  de `requirements.txt` (ver comentário no próprio arquivo para o motivo e o comando exato).


Instale as dependências com:
```bash
pip install -r requirements.txt
```

## Rodando o V1 (backend + frontend) localmente

Requer Docker e Docker Compose.

```bash
./scripts/start-linux.sh   # builda e sobe backend (FastAPI) + frontend (React)
./scripts/stop-linux.sh    # derruba os containers
```

Depois de subir:
- Frontend: http://localhost:5173
- Backend (API): http://localhost:8000 (docs interativos em `/docs`)

O backend usa um banco SQLite temporário, guardado em um volume Docker
(`backend_data`). O schema é gerenciado via Alembic (`backend/alembic/`), e a cada
inicialização o backend roda as migrações pendentes e sincroniza os dados a partir dos
CSVs em `backend/seed_data/` — não é mais um seed único na primeira execução, editar os
CSVs e reiniciar já é suficiente (ver [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md),
Fase 2).

### Rodando sem Docker (desenvolvimento)

```bash
# backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# frontend (em outro terminal)
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Pipeline de dados automatizado

Além do V1 (backend + frontend), o projeto tem um pipeline de dados real — scrape
incremental → algoritmo do cinturão → sync do banco → deploy — orquestrado com uma DAG
real do Airflow e agendado via GitHub Actions (scrape semanal que abre um PR com os
dados atualizados para revisão; nunca escreve direto em produção). Ver
[`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) para o plano completo, as decisões
tomadas e o status atual de cada fase.

Para rodar a DAG localmente (sem scheduler/webserver — `airflow dags test` roda tudo
num processo só):

```bash
pip install -r requirements.txt
pip install -r requirements-airflow.txt \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.12.txt"

export AIRFLOW_HOME=$(pwd)/.airflow-home
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/dags
export PYTHONPATH=$(pwd)   # necessário - ver CLAUDE.MD, "Pipeline orchestration"
airflow db migrate                      # uma vez
airflow dags reserialize
airflow dags test update_fabr_data "$(date -u +%Y-%m-%d)"
```

### Testes

```bash
cd backend && uv run pytest && uv run ruff check . && uv run mypy app
cd frontend && npm run test && npm run typecheck && npm run lint

# testes do pipeline de dados (raiz do repo)
python -m pytest tests/ --ignore=tests/scrapper_test.py --ignore=tests/get_urls_test.py
# scrapper_test.py/get_urls_test.py acessam o site ao vivo (salaooval.com.br) - rodar
# manualmente quando fizer sentido, não fazem parte do loop rápido de testes
```
