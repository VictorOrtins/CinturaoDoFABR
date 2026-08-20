import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Topbar } from "./components/Topbar";
import { AssistantPage } from "./pages/AssistantPage";
import { GamesPage } from "./pages/GamesPage";
import { HomePage } from "./pages/HomePage";
import { RulesPage } from "./pages/RulesPage";
import { StatsPage } from "./pages/StatsPage";
import { TeamDetailPage } from "./pages/TeamDetailPage";
import { TeamsPage } from "./pages/TeamsPage";
import { ThemeProvider } from "./theme/ThemeContext";
import "./App.css";

export function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="app-layout">
          <Topbar />
          <main className="app-layout__content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/jogos" element={<GamesPage />} />
              <Route path="/times" element={<TeamsPage />} />
              <Route path="/times/:id" element={<TeamDetailPage />} />
              <Route path="/regras" element={<RulesPage />} />
              <Route path="/estatisticas" element={<StatsPage />} />
              <Route path="/assistente" element={<AssistantPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
