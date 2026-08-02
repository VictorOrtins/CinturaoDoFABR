# Cinturão do Futebol Americano Brasileiro

## Metodologia

1. **Scraping de todas as partidas que já ocorreram no FABR**: Uso de bibliotecas de web scrapping para raspar dados do site Salão Oval com todas as partidas ocorridas no FABR
   
2. **Computar resultados**: A partir dos dados obtidos, a ideia é computar os resultados e ver quem está com o cinturão do FABR hoje.

3. **Análises relacionadas**: Além disso, serão feitas diversas análises sobre o cinturão, quem mais esteve com sua posse, quem mais desafiou o campeão, em conjunto com outras análises a definir.

4. **Criação de Web App**: Será feito um aplicativo para browsers para mostrar os resultados ao público.

## Estrutura do Projeto

- **`app/`**: Protótipo do aplicativo web utilizando Streamlit (mantido como referência).
- **`backend/`**: API do V1, em FastAPI (uv project) com um banco SQLite temporário, seedado a partir dos CSVs em `backend/seed_data/`.
- **`frontend/`**: Aplicativo web do V1, em React + Vite + TypeScript.
- **`scripts/`**: Scripts para subir/derrubar o projeto localmente via Docker.
- **`notebooks/`**: Notebooks Jupyter que documentam análises feitas em cima dos dados obtidos.
- **`src/`**: Contém os scripts Python para coleta de dados e cálculos estatísticos:
  - **`cinturao_algorithm/`**: Scripts do algoritmo do cinturão
  - **`preprocessing/`**: Scripts de pré-processamento dos dados advindos do scraping.
  - **`scraping/`**: Scripts para web scraping de todos os resultados históricos do FABR.
  - **`utils/`**: Funções em comum para todos os arquivos.
- **`tests/`**: Contém os testes unitários para arquivos necessários do teste
- **`README.md`**: Documento explicativo do repositório (você está aqui).
- **`requirements.txt`**: Dependências utilizadas no projeto (scraping/preprocessing/algoritmo)


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
(`backend_data`), populado automaticamente a partir dos CSVs em
`backend/seed_data/` na primeira inicialização.

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

### Testes

```bash
cd backend && uv run pytest && uv run ruff check . && uv run mypy app
cd frontend && npm run test && npm run typecheck && npm run lint
```
