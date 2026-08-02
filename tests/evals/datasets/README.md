# Evaluation Golden Datasets

This directory contains human-labeled golden datasets for regression testing of LLM components.

## Purpose

Phase 2 requires **calibrated evaluation** - the ability to detect when prompt/rubric changes cause performance regression. These datasets provide ground truth for automated testing.

## Dataset Categories

### 1. Scoring Golden (`scoring/`)
Human-labeled 6-dimension scores for answer evaluation.

**Schema**: Each case contains:
- `case_id`: Unique identifier
- `question`: Interview question text
- `answer`: Candidate's answer text
- `expected_scores`: Human-labeled scores for 6 dimensions
  - `technical_correctness` (0-25)
  - `implementation_depth` (0-20)
  - `architecture_tradeoffs` (0-15)
  - `personal_contribution` (0-15)
  - `production_awareness` (0-15)
  - `clarity` (0-10)
- `reasoning`: Why these scores were assigned
- `version`: Dataset version (v1.0)
- `labeled_by`: Annotator ID
- `labeled_at`: Timestamp

**Metrics**:
- MAE (Mean Absolute Error) per dimension
- Level agreement rate (±1 level tolerance)
- Dimension miss rate (score=0 when should be >0)

### 2. Routing Golden (`routing/`)
Expected next-action decisions after answer analysis.

**Schema**: Each case contains:
- `case_id`: Unique identifier
- `state`: Current interview state (turn_count, claim_status, contradictions, etc.)
- `latest_evaluation`: Last answer's evaluation
- `expected_action`: Human-labeled next action
  - `FOLLOW_UP` - Continue on same claim/depth
  - `CLARIFY` - Ask clarification question
  - `INCREASE_DIFFICULTY` - Move to higher depth
  - `SWITCH_CLAIM` - Move to different claim
  - `SWITCH_TOPIC` - Move to different topic
  - `COACHING` - Generate coaching
  - `FINISH` - End interview
- `reasoning`: Why this action is correct
- `version`: Dataset version (v1.0)

**Metrics**:
- Routing accuracy (exact match)
- Invalid route rate (outputs non-enum value)
- Premature switch rate (switches claim before verification)

### 3. Evidence Golden (`evidence/`)
Expected claim status transitions based on answers.

**Schema**: Each case contains:
- `case_id`: Unique identifier
- `claim`: Resume claim being verified
- `verification_point`: Specific aspect being checked
- `question`: Question asked
- `answer`: Candidate's answer
- `previous_status`: Claim status before this answer
- `expected_status`: Human-labeled status after this answer
  - `UNTOUCHED` - Not yet addressed
  - `IN_PROGRESS` - Partially addressed
  - `PARTIALLY_VERIFIED` - Some evidence exists
  - `VERIFIED` - Sufficient evidence
  - `CONTRADICTORY` - Conflicting statements
  - `UNSUPPORTED` - Insufficient evidence after probing
- `expected_strength`: Evidence strength (0-100)
- `reasoning`: Why this status is correct
- `version`: Dataset version (v1.0)

**Metrics**:
- Status accuracy (exact match)
- VERIFIED false positive rate (claims VERIFIED without evidence)
- UNSUPPORTED false negative rate (marks UNSUPPORTED too early)
- Contradiction detection precision/recall

## Creating Golden Datasets

### Initial Phase 1 Baseline (M2.0)
- **Goal**: 20-30 cases per category
- **Source**: Real Phase 1 interview transcripts + manual labeling
- **Focus**: Diverse scenarios (high/low scores, contradictions, edge cases)

### Expansion (M2.3)
- **Goal**: 50+ cases per category
- **Source**: Additional real interviews + adversarial cases
- **Focus**: Edge cases, prompt injection attempts, ambiguous answers

## Dataset Format

All datasets are stored as JSON files with `.jsonl` format (one case per line):

```jsonl
{"case_id": "scoring_001", "question": "...", "answer": "...", "expected_scores": {...}, ...}
{"case_id": "scoring_002", "question": "...", "answer": "...", "expected_scores": {...}, ...}
```

## Versioning

Datasets are versioned (`v1.0`, `v1.1`, etc.) to track changes:
- **Major version** (v1 → v2): Significant schema or labeling guideline changes
- **Minor version** (v1.0 → v1.1): New cases added, minor corrections

Always specify dataset version when running evals to ensure reproducibility.

## Privacy & Ethics

- All datasets are **anonymized** - no real names, companies, or identifying information
- Personal details are replaced with placeholders (`<COMPANY>`, `<PROJECT>`, `<NAME>`)
- Datasets are **not derived from production user data without explicit consent**
- Initial datasets use synthetic or consent-approved interview transcripts

## Usage

```python
from app.evals.datasets import load_golden_dataset

# Load scoring golden dataset
scoring_cases = load_golden_dataset("scoring", version="v1.0")

# Run evaluation
from app.evals.runner import run_scoring_eval
results = run_scoring_eval(scoring_cases, prompt_version="v2.1")
print(f"MAE: {results.mae}, Accuracy: {results.accuracy}")
```

## Contributing

When adding new cases:
1. Follow the schema exactly
2. Provide clear reasoning for labels
3. Include edge cases and adversarial examples
4. Increment dataset version appropriately
5. Run validation: `pytest tests/evals/test_dataset_schema.py`
