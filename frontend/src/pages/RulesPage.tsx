import "./RulesPage.css";

export function RulesPage() {
  return (
    <div className="rules-page">
      <p className="rules-page__eyebrow">Regulamento</p>
      <h1>Regras do Cinturão</h1>

      <section className="rules-page__section">
        <h2>Jogos Válidos</h2>
        <ol className="rules-list">
          <li>
            <p>
              Serão considerados apenas jogos de torneios oficiais presentes no site do Salão
              Oval. Jogos de possíveis categorias de base não serão considerados no futuro.
            </p>
            <ol className="rules-list--nested">
              <li>
                A única exceção a regra é a partida realizada no FABR Day entre Brown Spiders e
                Curitiba Crocodiles. Foi uma partida muito importante na história do FABR para
                ser deixada de lado.
              </li>
              <li>
                O Salão Oval é o banco de dados mais relevante de partidas do Futebol Americano
                no Brasil. Por isso o critério foi adotado.
              </li>
            </ol>
          </li>
          <li>
            <p>
              Os times principais dos times serão considerados diferentes dos times
              secundários/desenvolvimento.
            </p>
            <p className="rules-page__example">
              <span className="rules-page__example-label">Exemplo</span>
              Considere que o Recife Mariners é o atual detentor do cinturão. Caso o Recife
              Mariners Development jogue uma partida e perca, o Recife Mariners NÃO perde o
              cinturão. Os dois times nesse caso são considerados distintos.
            </p>
          </li>
          <li>
            <p>
              Caso, no futuro, tenhamos competições internacionais de clubes, serão considerados
              confrontos entre equipes brasileiras, mesmo que sediadas fora do Brasil.
            </p>
          </li>
        </ol>
      </section>

      <section className="rules-page__section">
        <h2>Troca do Cinturão</h2>
        <ol className="rules-list">
          <li>
            <p>
              A troca de cinturão ocorre quando o detentor do cinturão perde uma partida. O
              vencedor desta partida é agora o novo detentor do Cinturão do FABR.
            </p>
          </li>
          <li>
            <p>
              Caso o detentor do cinturão fique mais de 2 anos sem disputar uma partida oficial,
              ele perde o cinturão, que retorna ao detentor anterior ao detentor atual.
            </p>
            <p className="rules-page__example">
              <span className="rules-page__example-label">Exemplo</span>
              Considere que o Recife Mariners é o atual detentor, que ganhou o cinturão
              derrotando o Galo FA. Se, por acaso, o Mariners ficar mais de 2 anos sem jogar
              partidas oficiais, o cinturão volta para o Galo FA.
            </p>
            <ol className="rules-list--nested">
              <li>
                A única exceção a essa regra são períodos em que todo o FABR fica sem jogar
                partidas oficiais por motivos de força maior. Por exemplo, a pandemia da
                COVID-19.
              </li>
            </ol>
          </li>
        </ol>
      </section>
    </div>
  );
}
