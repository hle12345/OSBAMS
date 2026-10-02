# Model registry
`registry.py` appends one JSON line per trained model (`registry.jsonl`, created on first use): model type, dataset and feature versions,
training battery count, chemistry coverage, test protocol, validation metrics, explanation, limitations, and a `synthetic` flag. A registry
entry is a record of what was done, not a claim that the model is validated.
