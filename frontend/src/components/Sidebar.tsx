import { NavLink } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";
import "./Sidebar.css";

const NAV_LINKS = [
  { to: "/", label: "Início" },
  { to: "/jogos", label: "Jogos" },
  { to: "/regras", label: "Regras" },
  { to: "/estatisticas", label: "Estatísticas" },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <NavLink to="/" className="sidebar__brand">
        Cinturão
        <br />
        do FABR
      </NavLink>

      <nav className="sidebar__nav">
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              isActive ? "sidebar__link sidebar__link--active" : "sidebar__link"
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <ThemeToggle />
      </div>
    </aside>
  );
}
