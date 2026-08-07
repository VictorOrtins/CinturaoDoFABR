import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CurrentChampion } from "../api/types";
import { ChampionCard } from "../components/ChampionCard";
import { LoadingBelt } from "../components/LoadingBelt";
import "./HomePage.css";

export function HomePage() {
  const [champion, setChampion] = useState<CurrentChampion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getCurrentChampion()
      .then(setChampion)
      .catch(() => setError("Não foi possível carregar o atual detentor do cinturão."));
  }, []);

  return (
    <div className="home-page">
      <h1 className="home-page__title">Cinturão do Futebol Americano Brasileiro</h1>

      <h2>O que é o Cinturão do FABR</h2>
      <p>
        E se o futebol americano brasileiro fosse estruturado de uma maneira completamente
        diferente? Em vez de títulos decididos por temporadas e playoffs, o campeão só poderia
        ser coroado ao derrotar o atual detentor do cinturão. Nesse modelo, inspirado no boxe, a
        equipe que conquista o título precisa defendê-lo a cada jogo contra novos desafiantes,
        tornando cada partida uma verdadeira disputa pelo domínio do esporte.
      </p>
      <p>
        Essa é a essência do Cinturão do Futebol Americano Brasileiro: um título que não se ganha
        em uma temporada perfeita ou em um torneio eliminatório, mas sim no campo, jogo após
        jogo, com cada campeão precisando provar sua superioridade todas as vezes que entrar em
        campo.
      </p>
      <p>
        A primeira partida considerada para o cinturão não poderia ser outra: o FABR Day. No dia
        25 de outubro de 2008, Curitiba Brown Spiders (hoje só Brown Spiders) e Barigui
        Crocodiles (hoje Coritiba Crocodiles) protagonizaram o primeiro jogo full pad em solo
        brasileiro. Venceu o Brown Spiders, que se sagrou o primeiro detentor do Cinturão do
        FABR.
      </p>
      <p>
        As próximas partidas consideradas para o cinturão foram apenas em torneios oficiais.
        Sendo assim, o Brown Spiders defendeu o cinturão no jogo seguinte, no dia 07 de agosto de
        2009, contra o Joinville Gladiators, e venceu, mantendo o título.
      </p>
      <p>
        Na partida seguinte, porém, em 22 de agosto de 2009, o Coritiba Crocodiles derrotou o
        Brown Spiders por 23x20 e se sagrou o novo detentor do cinturão do FABR. E assim se
        sucedeu, até o presente.
      </p>

      <h2>Atual Detentor 🏆</h2>
      <div className="home-page__champion">
        {champion && <ChampionCard champion={champion} />}
        {error && <p className="home-page__status">{error}</p>}
        {!champion && !error && <LoadingBelt />}
      </div>
    </div>
  );
}
