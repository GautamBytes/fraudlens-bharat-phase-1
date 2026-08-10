const STEPS = [
  ["01", "Input", "Synthetic text or screenshot"],
  ["02", "Signals", "Entities, URLs and urgency"],
  ["03", "Decision", "Category with uncertainty"],
  ["04", "Action", "Reviewable complaint draft"],
] as const;

export function EvidenceRail({ activeStep }: { activeStep: number }) {
  return (
    <ol className="evidenceRail" aria-label="Analysis stages">
      {STEPS.map(([number, title, detail], index) => (
        <li
          className={index + 1 <= activeStep ? "railStep railStepActive" : "railStep"}
          key={number}
        >
          <span className="railNumber">{number}</span>
          <span>
            <strong>{title}</strong>
            <small>{detail}</small>
          </span>
        </li>
      ))}
    </ol>
  );
}
