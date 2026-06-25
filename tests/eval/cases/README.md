# Eval Test Cases

Each domain has its own JSON file. Domain owners add test cases to their file.

## Adding Test Cases

1. Open `cases/{your-domain}.json`
2. Add entries:

```json
{"prompt": "Your natural language query", "operation": "expected_operation_name"}
```

3. Commit and push — CI will run the eval automatically

## Format

| Field | Description |
|-------|-------------|
| `prompt` | What a user would say (natural language) |
| `operation` | The expected `operationId` that should be called |

The skill name is inferred from the filename: `pricing.json` → `fpr-pricing`.

## Running Locally

```bash
# Keyword baseline (fast, deterministic)
python tests/eval/test_skill_accuracy.py

# LLM eval with Gemini (slower, more realistic)
python tests/eval/test_skill_accuracy.py --llm
```

## Tips for Good Test Cases

- Use realistic user phrasing (not just operation names)
- Include variations: "budget", "remaining budget", "how much budget left"
- Include ambiguous cases to test disambiguation
- Aim for 5-10 cases per operation
