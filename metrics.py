import argparse
import json
import statistics
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("model", help="Exemplo: qwen2.5:7b")
args = parser.parse_args()

model_file = args.model.replace(":", "-")

input_file = Path("results") / f"{model_file}.jsonl"
output_file = Path("results") / f"{model_file}-metrics.json"


def time_metrics(values):
    return {
        "total_seconds": sum(values),
        "mean_seconds": statistics.mean(values),
        "median_seconds": statistics.median(values),
        "minimum_seconds": min(values),
        "maximum_seconds": max(values),
    }


wall_times = []
total_durations = []
input_tokens = []
output_tokens = []
ignored = 0


with input_file.open(encoding="utf-8") as file:
    for line in file:
        if not line.strip():
            continue

        record = json.loads(line)

        if record.get("error"):
            ignored += 1
            continue

        wall_time = record.get("wall_time")
        total_duration = record.get("total_duration")
        prompt_tokens = record.get("prompt_eval_count")
        generated_tokens = record.get("eval_count")

        if wall_time is not None:
            wall_times.append(float(wall_time))

        if total_duration is not None:
            total_durations.append(
                float(total_duration) / 1_000_000_000
            )

        if prompt_tokens is not None:
            input_tokens.append(int(prompt_tokens))

        if generated_tokens is not None:
            output_tokens.append(int(generated_tokens))


tokens_per_total_second = (
    sum(output_tokens) / sum(total_durations)
    if total_durations
    else None
)


metrics = {
    "model": args.model,
    "valid_records": len(wall_times),
    "ignored_records": ignored,
    "wall_time": time_metrics(wall_times),
    "total_duration": time_metrics(total_durations),
    "mean_input_tokens": statistics.mean(input_tokens),
    "mean_output_tokens": statistics.mean(output_tokens),
    "output_tokens_per_total_second": tokens_per_total_second,
}


with output_file.open("w", encoding="utf-8") as file:
    json.dump(
        metrics,
        file,
        ensure_ascii=False,
        indent=2,
    )


print(f"Modelo: {args.model}")
print(f"Registros válidos: {metrics['valid_records']}")
print(f"Registros ignorados: {ignored}")

print(
    f"Tokens médios de entrada: "
    f"{metrics['mean_input_tokens']:.2f}"
)

print(
    f"Tokens médios de saída: "
    f"{metrics['mean_output_tokens']:.2f}"
)

print(
    f"Tokens de saída por segundo total: "
    f"{tokens_per_total_second:.2f}"
)

print(f"Métricas salvas em: {output_file}")