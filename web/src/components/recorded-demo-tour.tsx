import Image from "next/image";
import Link from "next/link";

const STORIES = [
  {
    step: "01",
    title: "Classify a suspicious message",
    label: "Text analysis",
    image: "/showcase/text-analysis.png",
    width: 1180,
    height: 1282,
    alt: "Completed text analysis with a KYC scam decision and supporting signals",
    input: "A synthetic KYC-expiry message with an external verification link.",
    output: "A calibrated category, confidence, risk score, masked URL evidence and complaint draft.",
    inspect: "Check that the decision remains separate from the evidence and human-review boundary.",
    href: "/analyze",
    linkLabel: "Open analysis",
  },
  {
    step: "02",
    title: "Extract evidence from a screenshot",
    label: "Screenshot + OCR",
    image: "/showcase/screenshot-analysis.png",
    width: 1180,
    height: 1421,
    alt: "Completed screenshot analysis with extracted OCR text and review evidence",
    input: "A bounded synthetic PNG containing English fraud-message text.",
    output: "In-memory OCR text, source metadata and the same explainable review result used for messages.",
    inspect: "Confirm the source image is discarded and only consented derived evidence can be retained.",
    href: "/analyze",
    linkLabel: "Open analysis",
  },
  {
    step: "03",
    title: "Connect repeated masked signals",
    label: "Relationship intelligence",
    image: "/showcase/relationship-graph.png",
    width: 1180,
    height: 1163,
    alt: "Two synthetic reports linked through one repeated masked URL",
    input: "Two synthetic reports that reuse one controlled campaign URL.",
    output: "Two case nodes, one masked entity and a complete two-edge evidence ledger.",
    inspect: "Treat every edge as observed co-occurrence—not an automatic fraud decision.",
    href: "/relationships",
    linkLabel: "Open relationships",
  },
] as const;

function RecordedDemoStory({ story, reverse }: { story: (typeof STORIES)[number]; reverse: boolean }) {
  return (
    <article className={reverse ? "recordedStory recordedStoryReverse" : "recordedStory"}>
      <div className="recordedStoryCopy">
        <div className="recordedStoryMeta"><span>{story.step}</span><strong>Recorded synthetic demonstration</strong></div>
        <p className="eyebrow">{story.label}</p>
        <h3>{story.title}</h3>
        <dl>
          <div><dt>Input</dt><dd>{story.input}</dd></div>
          <div><dt>Output</dt><dd>{story.output}</dd></div>
          <div><dt>Inspect</dt><dd>{story.inspect}</dd></div>
        </dl>
        <Link className="quietLink" href={story.href}>{story.linkLabel} <span>→</span></Link>
      </div>
      <div className="recordedFrame">
        <div className="recordedFrameTop"><span /><span /><span /><small>fraudlens.local · recorded</small></div>
        <Image src={story.image} alt={story.alt} width={story.width} height={story.height} sizes="(max-width: 860px) calc(100vw - 32px), 58vw" />
      </div>
    </article>
  );
}

export function RecordedDemoTour() {
  return (
    <section className="homeSection recordedTour" aria-labelledby="recorded-tour-title">
      <header className="recordedTourHeading">
        <div><p className="eyebrow">Recorded product path</p><h2 id="recorded-tour-title">See the system before you run it.</h2></div>
        <p>These screenshots replay controlled synthetic fixtures through the current interface. They demonstrate workflow and evidence structure, not production accuracy.</p>
      </header>
      <div className="recordedStories">
        {STORIES.map((story, index) => <RecordedDemoStory key={story.step} story={story} reverse={index % 2 === 1} />)}
      </div>
    </section>
  );
}
