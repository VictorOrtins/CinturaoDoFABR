# Cinturão do Futebol Americano Brasileiro

## Metodologia

1. **Scraping de todas as partidas que já ocorreram no FABR**: Uso de bibliotecas de web scrapping para raspar dados do site Salão Oval com todas as partidas ocorridas no FABR
   
2. **Computar resultados**: A partir dos dados obtidos, a ideia é computar os resultados e ver quem está com o cinturão do FABR hoje.

3. **Análises relacionadas**: Além disso, serão feitas diversas análises sobre o cinturão, quem mais esteve com sua posse, quem mais desafiou o campeão, em conjunto com outras análises a definir.

4. **Criação de Web App**: Será feito um aplicativo para browsers para mostrar os resultados ao público.

## Estrutura do Projeto

- **`app/`**: Aplicativo para browser utilizando streamlit que documenta os resultados encontrados.
- **`notebooks/`**: Notebooks Jupyter que documentam análises feitas em cima dos dados obtidos.
- **`src/`**: Contém os scripts Python para coleta de dados e cálculos estatísticos:
  - **`cinturao_algorithm/`**: Scripts do algoritmo do cinturão
  - **`preprocessing/`**: Scripts de pré-processamento dos dados advindos do scraping.
  - **`scraping/`**: Scripts para web scraping de todos os resultados históricos do FABR.
  - **`utils/`**: Funções em comum para todos os arquivos.
- **`tests/`**: Contém os testes unitários para arquivos necessários do teste
- **`README.md`**: Documento explicativo do repositório (você está aqui).
- **`requirements.txt`**: Dependências utilizadas no projeto 


Instale as dependências com:
```bash
pip install -r requirements.txt
