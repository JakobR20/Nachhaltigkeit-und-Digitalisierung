import Link from "next/link";

export function Header({ subtitle }: { subtitle?: string }) {
  return (
    <div className="mb-5 flex items-start justify-between">
      <div>
        <h1 className="text-[28px] font-bold leading-none text-hig-text">THWS</h1>
        <p className="text-[15px] text-hig-secondary">
          Nachhaltigkeit &amp; Digitalisierung
        </p>
        {subtitle && (
          <p className="mt-2 text-[17px] font-medium text-hig-text">{subtitle}</p>
        )}
      </div>
      <Link
        href="/research"
        aria-label="Forschungs-Ansicht"
        className="text-2xl text-hig-secondary transition-colors hover:text-hig-accent"
      >
        ⚙
      </Link>
    </div>
  );
}
