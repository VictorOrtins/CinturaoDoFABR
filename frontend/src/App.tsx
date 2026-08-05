import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { GamesPage } from "./pages/GamesPage";
import { HomePage } from "./pages/HomePage";
import { RulesPage } from "./pages/RulesPage";
import { StatsPage } from "./pages/StatsPage";
import { ThemeProvider } from "./theme/ThemeContext";
import "./App.css";

export function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="app-layout">
          <Sidebar />
          <main className="app-layout__content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/jogos" element={<GamesPage />} />
              <Route path="/regras" element={<RulesPage />} />
              <Route path="/estatisticas" element={<StatsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
