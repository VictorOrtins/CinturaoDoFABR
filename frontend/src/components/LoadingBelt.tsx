import { BeltIcon } from "./BeltIcon";
import "./LoadingBelt.css";

interface LoadingBeltProps {
  label?: string;
}

export function LoadingBelt({ label = "Carregando..." }: LoadingBeltProps) {
  return (
    <div className="loading-belt" role="status" aria-live="polite">
      <span className="loading-belt__ring">
        <BeltIcon size={28} className="loading-belt__icon" />
      </span>
      {label && <span className="loading-belt__label">{label}</span>}
    </div>
  );
}
