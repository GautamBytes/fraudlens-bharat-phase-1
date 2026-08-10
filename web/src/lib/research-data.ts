import snapshot from "./research-snapshot.json";

export const RESEARCH_SNAPSHOT = snapshot;

export const RESEARCH_MODELS = [
  { name: "Rule baseline", role: "Reference", ...snapshot.models.rule_only, weakness: "High precision on explicit patterns, but misses paraphrases and unseen wording." },
  { name: "Word TF–IDF + logistic regression", role: "Baseline", ...snapshot.models.word_tfidf_logistic_regression, weakness: "Readable word features, but brittle to spelling and transliterated variants." },
  { name: "Character TF–IDF + logistic regression", role: "Experimental candidate", ...snapshot.models.character_tfidf_logistic_regression, weakness: "Best internal score, but not selected for runtime calibration and abstention behavior." },
  { name: "Word + character TF–IDF", role: "Experimental candidate", ...snapshot.models.word_character_tfidf_logistic_regression, weakness: "Matches the character candidate on this very small split; more evidence is needed to distinguish them." },
  { name: "Calibrated TF–IDF runtime", role: "Deployed", ...snapshot.models.deployed_runtime, weakness: "Lower headline score, but exposes uncertainty and abstains instead of forcing every decision." },
] as const;

export const RESEARCH_PARAMETERS = [
  { name: "Accuracy", explanation: "Easy to interpret, but can hide weak minority-class performance." },
  { name: "Macro-F1", explanation: "Macro-F1 weights every scam class equally, so a common class cannot dominate the score." },
  { name: "Coverage", explanation: "Coverage shows how often the model is willing to decide after confidence-based abstention." },
  { name: "Accepted accuracy", explanation: "Measures correctness only where the calibrated system accepts its own prediction." },
  { name: "Robustness delta", explanation: "Compares clean and perturbed text to expose dependence on punctuation, spacing and spelling." },
] as const;
