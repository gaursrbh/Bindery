export default function StatTrio({ props }) {
  return (
    <div className="bindery-stat-trio">
      {props.stats.map((s, i) => {
        const body = (
          <>
            <div className="bindery-stat-value" style={{ color: "var(--color-primary)" }}>
              {s.value}
            </div>
            <div className="bindery-stat-label" style={{ color: "var(--color-neutral)" }}>
              {s.label}
            </div>
            {s.delta && (
              <div className="bindery-stat-delta" style={{ color: "var(--color-secondary)" }}>
                {s.delta}
              </div>
            )}
          </>
        );
        return s.href ? (
          <a key={i} className="bindery-stat" href={s.href}>
            {body}
          </a>
        ) : (
          <div key={i} className="bindery-stat">
            {body}
          </div>
        );
      })}
    </div>
  );
}
