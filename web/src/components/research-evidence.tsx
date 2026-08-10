import { RESEARCH_MODELS, RESEARCH_PARAMETERS } from "@/lib/research-data";

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="researchMetric"><span>{label}</span><strong>{(value * 100).toFixed(1)}%</strong></div>;
}

export function ResearchEvidence() {
  const candidate = RESEARCH_MODELS[2];
  const deployed = RESEARCH_MODELS[4];

  return (
    <div className="researchStack">
      <section className="researchComparison" aria-label="Primary model comparison">
        <article className="researchHeroCard candidateCard">
          <p className="eyebrow">Highest internal score</p>
          <h2>Experimental candidate</h2>
          <h3>{candidate.name}</h3>
          <div className="researchMetrics"><Metric label="Accuracy" value={candidate.accuracy} /><Metric label="Macro-F1" value={candidate.macroF1} /></div>
          <p>{candidate.weakness}</p>
        </article>
        <article className="researchHeroCard deployedCard">
          <p className="eyebrow">What the demo actually runs</p>
          <h2>Deployed calibrated model</h2>
          <h3>{deployed.name}</h3>
          <div className="researchMetrics"><Metric label="Accuracy" value={deployed.accuracy} /><Metric label="Coverage" value={deployed.coverage} /></div>
          <p>{deployed.weakness}</p>
        </article>
      </section>

      <div className="evidenceCaveat">
        <strong>Evidence boundary</strong>
        <span>8 synthetic test rows, one row per class. This is internal comparative evidence, not a production accuracy claim.</span>
      </div>

      <section className="researchSection">
        <div className="sectionIntro"><p className="eyebrow">All evaluated approaches</p><h2>Same split, different trade-offs</h2></div>
        <div className="modelTableWrap">
          <table className="modelTable">
            <thead><tr><th>Approach</th><th>Role</th><th>Accuracy</th><th>Macro-F1</th><th>Coverage</th><th>Primary weakness</th></tr></thead>
            <tbody>{RESEARCH_MODELS.map((model) => <tr key={model.name}><th>{model.name}</th><td><span className={`rolePill role-${model.role.toLowerCase().replaceAll(" ", "-")}`}>{model.role}</span></td><td>{(model.accuracy * 100).toFixed(1)}%</td><td>{(model.macroF1 * 100).toFixed(1)}%</td><td>{(model.coverage * 100).toFixed(1)}%</td><td>{model.weakness}</td></tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className="researchSection">
        <div className="sectionIntro"><p className="eyebrow">Evaluation design</p><h2>Why these parameters matter</h2></div>
        <div className="parameterGrid">{RESEARCH_PARAMETERS.map((parameter, index) => <article key={parameter.name}><span>{String(index + 1).padStart(2, "0")}</span><h3>{parameter.name}</h3><p>{parameter.explanation}</p></article>)}</div>
      </section>
    </div>
  );
}
