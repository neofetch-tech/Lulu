import "./ActivityPulse.css";

interface Props {
  active: boolean;
}

/**
 * Five bars that idle as a flat, low hum and rise into an irregular
 * waveform while a response is generating — a small, honest signal that
 * inference is actually happening on this machine right now, not a
 * decorative loading spinner.
 */
export function ActivityPulse({ active }: Props) {
  return (
    <div className={`pulse ${active ? "pulse--active" : ""}`} aria-hidden="true">
      {[0, 1, 2, 3, 4].map((i) => (
        <span key={i} className="pulse__bar" style={{ animationDelay: `${i * 90}ms` }} />
      ))}
    </div>
  );
}
