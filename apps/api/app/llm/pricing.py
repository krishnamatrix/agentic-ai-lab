BENCHMARK_INPUT_PRICE_PER_1M = 0.50
BENCHMARK_OUTPUT_PRICE_PER_1M = 1.50


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Estimate API cost for a given number of input and output tokens.
    """
    input_cost = (input_tokens / 1_000_000) * BENCHMARK_INPUT_PRICE_PER_1M
    output_cost = (output_tokens / 1_000_000) * BENCHMARK_OUTPUT_PRICE_PER_1M
    return input_cost + output_cost
