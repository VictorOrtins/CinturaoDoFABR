import { NavLink } from "react-router-dom";
import "./Navbar.css";

const NAV_LINKS = [
  { to: "/", label: "Início" },
  { to: "/jogos", label: "Jogos" },
  { to: "/regras", label: "Regras" },
  { to: "/estatisticas", label: "Estatísticas" },
];

export function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar__brand">
        Cinturão do FABR
      </NavLink>
      {NAV_LINKS.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.to === "/"}
          className={({ isActive }) =>
            isActive ? "navbar__link navbar__link--active" : "navbar__link"
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
