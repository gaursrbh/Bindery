export default function NavBar({ props }) {
  return (
    <nav className="bindery-nav-bar" style={{ borderColor: "var(--color-neutral)" }}>
      {props.links.map((l, i) => (
        <a key={i} href={l.href} style={{ color: "var(--color-text)" }}>
          {l.label}
        </a>
      ))}
    </nav>
  );
}
