import { RESEARCH_MODELS, RESEARCH_PARAMETERS, RESEARCH_SNAPSHOT } from "@/lib/research-data";

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="researchMetric"><span>{label}</span><strong>{(value * 100).toFixed(1)}%</strong></div>;
}

function modelSize(model: (typeof RESEARCH_MODELS)[number]): string {
  const bytes = "artifact_bytes" in model ? model.artifact_bytes : model.estimated_model_bytes;
  return bytes === 0 ? "Rules only" : `${(bytes / 1024).toFixed(0)} KB`;
}

export function ResearchEvidence() {
  const candidate = RESEARCH_MODELS[2];
  const deployed = RESEARCH_MODELS[4];
  const metricSignals = [
    { label: "Accuracy", candidate: candidate.accuracy, deployed: deployed.accuracy },
    { label: "Macro-F1", candidate: candidate.macro_f1, deployed: deployed.macro_f1 },
    { label: "Coverage", candidate: candidate.coverage, deployed: deployed.coverage },
  ];

  return (
    <div className="researchStack">
      <section className="researchComparison" aria-label="Primary model comparison" id="comparison">
        <article className="researchHeroCard candidateCard">
          <p className="eyebrow">Highest internal score</p>
          <h2>Experimental candidate</h2>
          <h3>{candidate.name}</h3>
          <div className="researchMetrics"><Metric label="Accuracy" value={candidate.accuracy} /><Metric label="Macro-F1" value={candidate.macro_f1} /></div><div className="modelSize">Estimated fitted size · {modelSize(candidate)}</div>
          <p>{candidate.weakness}</p>
        </article>
        <article className="researchHeroCard deployedCard">
          <p className="eyebrow">What the demo actually runs</p>
          <h2>Deployed calibrated model</h2>
          <h3>{deployed.name}</h3>
          <div className="researchMetrics"><Metric label="Accuracy" value={deployed.accuracy} /><Metric label="Coverage" value={deployed.coverage} /></div><div className="modelSize">Committed artifact bundle · {modelSize(deployed)}</div>
          <p>{deployed.weakness}</p>
        </article>
      </section>

      <section className="researchSignal" aria-label="Research metric signal">
        <div className="researchSignalIntro">
          <p className="eyebrow">Visual comparison</p>
          <h2>Accuracy is only one part of the decision</h2>
          <p>These same-split signals explain why the highest-scoring experiment is reported separately from the conservative runtime used in the demo.</p>
        </div>
        <div className="researchSignalGrid">
          {metricSignals.map((metric) => (
            <article className="researchSignalMetric" key={metric.label}>
              <h3>{metric.label}</h3>
              <div className="metricSignalRow"><span>Candidate</span><div className="metricSignalTrack"><i className="metricSignalCandidate" style={{ width: `${metric.candidate * 100}%` }} /></div><b>{(metric.candidate * 100).toFixed(1)}%</b></div>
              <div className="metricSignalRow"><span>Runtime</span><div className="metricSignalTrack"><i className="metricSignalRuntime" style={{ width: `${metric.deployed * 100}%` }} /></div><b>{(metric.deployed * 100).toFixed(1)}%</b></div>
            </article>
          ))}
        </div>
      </section>

      <div className="evidenceCaveat">
        <strong>Evidence boundary</strong>
        <span>{RESEARCH_SNAPSHOT.dataset.rows}-row synthetic fraud-only bootstrap; {RESEARCH_SNAPSHOT.dataset.test_rows} test rows, one per class; no legitimate label. This is internal comparative evidence, not a production accuracy claim.</span>
      </div>

      <details className="methodologyDetails">
        <summary>Methodology and validity checks</summary>
        <div>
          <p>All approaches use the same frozen, stratified internal split so their relative comparison is reproducible. The deployed runtime is reported separately because calibration and abstention change how often it accepts a decision.</p>
          <ul><li>One held-out synthetic example per fraud class.</li><li>No legitimate-message class, field trial, or population prevalence estimate.</li><li>Robustness checks perturb punctuation, spacing, and spelling.</li><li>Artifact sizes describe implementation cost, not predictive quality.</li></ul>
        </div>
      </details>

      <section className="researchSection" id="approaches">
        <div className="sectionIntro"><p className="eyebrow">All evaluated approaches</p><h2>Same split, different trade-offs</h2></div>
        <div className="modelTableWrap" tabIndex={0} aria-label="Model comparison table; scroll horizontally on small screens">
          <table className="modelTable">
            <caption className="visuallyHidden">Same-split classification benchmark and model trade-offs</caption>
            <thead><tr><th>Approach</th><th>Role</th><th>Accuracy</th><th>Macro-F1</th><th>Coverage</th><th>Size</th><th>Primary weakness</th></tr></thead>
            <tbody>{RESEARCH_MODELS.map((model) => <tr key={model.name}><th>{model.name}</th><td><span className={`rolePill role-${model.role.toLowerCase().replaceAll(" ", "-")}`}>{model.role}</span></td><td>{(model.accuracy * 100).toFixed(1)}%</td><td>{(model.macro_f1 * 100).toFixed(1)}%</td><td>{(model.coverage * 100).toFixed(1)}%</td><td>{modelSize(model)}</td><td>{model.weakness}</td></tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className="researchSection" id="parameters">
        <div className="sectionIntro"><p className="eyebrow">Evaluation design</p><h2>Why these parameters matter</h2></div>
        <div className="parameterGrid">{RESEARCH_PARAMETERS.map((parameter, index) => <article key={parameter.name}><span>{String(index + 1).padStart(2, "0")}</span><h3>{parameter.name}</h3><p>{parameter.explanation}</p></article>)}</div>
      </section>
    </div>
  );
}
