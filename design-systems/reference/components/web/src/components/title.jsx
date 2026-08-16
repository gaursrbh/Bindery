export default function Title({ props }) {
  return (
    <div className="bindery-title">
      {props.eyebrow && (
        <p
          className="bindery-eyebrow"
          style={{ color: `var(--color-${props.accent || "primary"})` }}
        >
          {props.eyebrow.toUpperCase()}
        </p>
      )}
      <h1 style={{ color: "var(--color-text)" }}>{props.headline}</h1>
    </div>
  );
}
