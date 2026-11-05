# Lesson 1 Experiment — Basic Generation and Inference Performance

## Objective

Measure how prompt/output size and model loading affect LLM latency,
throughput, and estimated token cost using Ollama and Gemma 4.

## Environment

- Provider: Ollama
- Model: gemma4:e4b
- Execution: Local
- Temperature: 0.0

## Experiment A — CRM Explanation

Prompt:

> Explain what a CRM is in one sentence.

Results:

- Input tokens: 24
- Output tokens: 318
- Total tokens: 342
- End-to-end latency: 9371.03 ms
- Model load: 3394.27 ms
- Prompt evaluation: 155.79 ms
- Generation: 5771.05 ms
- End-to-end throughput: 33.93 tokens/sec
- Generation throughput: 55.10 tokens/sec
- Estimated benchmark cost: $0.000489

## Experiment B — Minimal Output

Prompt:

> Reply with exactly: CRM.

Results:

- Input tokens: 22
- Output tokens: 3
- Total tokens: 25
- End-to-end latency: 293.74 ms
- Model load: 8.29 ms
- Prompt evaluation: 179.89 ms
- Generation: 51.34 ms
- End-to-end throughput: 10.21 tokens/sec
- Generation throughput: 58.44 tokens/sec
- Estimated benchmark cost: $0.0000155

## Observations

### Model loading

The first experiment incurred approximately 3.4 seconds
of model-loading time.

The second request incurred only approximately 8 ms,
indicating that the model was already resident.

### Generation throughput

Generation throughput was approximately 55–58 tokens/sec
across the two experiments.

This suggests that the large difference in generation latency
was primarily driven by the number of generated tokens.

### Output length

The first request generated 318 tokens while the second
generated only 3 tokens.

The benchmark token cost therefore differed substantially
even though the input sizes were similar.

### Important interpretation

`eval_count` is treated as the number of generated/evaluated
tokens reported by Ollama.

We do not assume that this represents hidden reasoning tokens,
visible text tokens, or any other semantic category without
provider-specific evidence.

## Engineering Lessons

1. Cold-start/model-loading latency and inference latency are different.
2. End-to-end throughput and generation throughput are different metrics.
3. Output length materially affects latency and token economics.
4. Local inference still has measurable resource and performance characteristics.
5. Provider telemetry should be preserved before being normalized.
6. LLM observability needs more than a single latency number.