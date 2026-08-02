import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { colors } from "../theme/colors";
import "./StatsPage.css";

// Placeholder data only — this page is a visual mock for the layout/design
// direction. Real stats endpoints are intentionally out of scope for this ticket.
const MOCK_DEFENSES = [
  { team: "Recife Mariners", defenses: 8 },
  { team: "Brown Spiders", defenses: 6 },
  { team: "Coritiba Crocodiles", defenses: 5 },
  { team: "Galo FA", defenses: 4 },
  { team: "JEC Gladiators", defenses: 3 },
];

export function StatsPage() {
  return (
    <div className="stats-page">
      <h1>Estatísticas</h1>
      <span className="stats-page__badge">Em breve</span>
      <p>
        Esta página vai reunir as estatísticas do Cinturão do FABR — como defesas de título,
        maiores detentores e sequências de vitórias. O layout abaixo é um mockup com dados de
        exemplo, ainda não conectado aos dados reais.
      </p>

      <div className="stats-page__mock">
        <h2>Times com mais defesas de título (exemplo)</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={MOCK_DEFENSES} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" allowDecimals={false} />
            <YAxis type="category" dataKey="team" width={140} />
            <Bar dataKey="defenses" fill={colors.bluePrimary} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
