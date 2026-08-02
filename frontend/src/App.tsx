import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { GamesPage } from "./pages/GamesPage";
import { HomePage } from "./pages/HomePage";
import { RulesPage } from "./pages/RulesPage";
import { StatsPage } from "./pages/StatsPage";

export function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/jogos" element={<GamesPage />} />
        <Route path="/regras" element={<RulesPage />} />
        <Route path="/estatisticas" element={<StatsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
