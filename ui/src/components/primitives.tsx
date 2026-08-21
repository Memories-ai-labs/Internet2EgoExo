/** The handful of primitives every panel is built from. */

import type { ReactNode } from "react";

export function Panel({
  title,
  meta,
  action,
  children,
}: {
  title: string;
  meta?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="panel">
      <header className="panel__head">
        <h2 className="panel__title">{title}</h2>
        {action ?? (meta ? <span className="panel__meta">{meta}</span> : null)}
      </header>
      {children}
    </section>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      {children}
    </label>
  );
}

export function Stat({
  label,
  value,
  note,
  small,
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  small?: boolean;
}) {
  return (
    <div className="stat">
      <span className="stat__label">{label}</span>
      <span className={small ? "stat__value stat__value--small" : "stat__value"}>{value}</span>
      {note ? <span className="stat__note">{note}</span> : null}
    </div>
  );
}

export type PillTone = "pass" | "fail" | "warn" | "muted" | "plain";

export function Pill({ tone = "plain", children }: { tone?: PillTone; children: ReactNode }) {
  const className = tone === "plain" ? "pill" : `pill pill--${tone}`;
  return <span className={className}>{children}</span>;
}

export function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button type="button" className="chip" aria-pressed={active} onClick={onClick}>
      {children}
    </button>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
