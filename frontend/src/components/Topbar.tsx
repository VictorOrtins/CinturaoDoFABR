import { NavLink } from "react-router-dom";
import { BeltIcon } from "./BeltIcon";
import { ThemeToggle } from "./ThemeToggle";
import "./Topbar.css";

const NAV_LINKS = [
  { to: "/", label: "Início" },
  { to: "/jogos", label: "Jogos" },
  { to: "/times", label: "Times" },
  { to: "/regras", label: "Regras" },
  { to: "/estatisticas", label: "Estatísticas" },
];

export function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar__inner">
        <NavLink to="/" className="topbar__brand">
          <BeltIcon size={26} className="topbar__brand-icon" />
          <span>Cinturão do FABR</span>
        </NavLink>

        <nav className="topbar__nav">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                isActive ? "topbar__link topbar__link--active" : "topbar__link"
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="topbar__actions">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
