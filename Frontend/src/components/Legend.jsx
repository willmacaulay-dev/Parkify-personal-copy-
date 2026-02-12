export default function Legend() {
  return (
    <div style={styles.card}>
      <div style={styles.title}>Legend</div>

      <div style={styles.item}>
        <span style={{ ...styles.dot, background: "#2e7d32" }} />
        <span>Low utilization</span>
      </div>

      <div style={styles.item}>
        <span style={{ ...styles.dot, background: "#f9a825" }} />
        <span>Medium utilization</span>
      </div>

      <div style={styles.item}>
        <span style={{ ...styles.dot, background: "#c62828" }} />
        <span>High utilization</span>
      </div>
    </div>
  );
}

const styles = {
  card: {
    borderRadius: 14,
    padding: 12,
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.08)",
  },
  title: { fontWeight: 800, marginBottom: 10, fontSize: 14 },
  item: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    fontSize: 13,
    marginBottom: 8,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.7)",
    boxShadow: "0 6px 14px rgba(0,0,0,0.35)",
  },
  note: { marginTop: 8, fontSize: 12, opacity: 0.75, lineHeight: 1.3 },
};
