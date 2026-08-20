interface BeltIconProps {
  size?: number;
  className?: string;
}

export function BeltIcon({ size = 24, className }: BeltIconProps) {
  return (
    <svg
      viewBox="0 0 64 40"
      width={size}
      height={(size * 40) / 64}
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M2 20 H20" />
      <path d="M44 20 H62" />
      <rect x="18" y="6" width="28" height="28" rx="6" />
      <path d="M32 14l2.5 5.2 5.7.8-4.1 4 1 5.7-5.1-2.7-5.1 2.7 1-5.7-4.1-4 5.7-.8Z" />
    </svg>
  );
}
