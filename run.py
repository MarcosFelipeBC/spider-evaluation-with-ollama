import argparse
import json
import time
from pathlib import Path

from tqdm import tqdm

from src.schema import get_schema
from src.prompt import create_prompt
from src.ollama_client import generate
from src.cleaner import clean_sql


parser = argparse.ArgumentParser()
parser.add_argument("model", help="Exemplo: qwen2.5-coder:7b")
args = parser.parse_args()

MODEL = args.model
TEST_LIMIT = None  # None para rodar as 2147 perguntas

DATASET_FILE = Path("data/boakpe/test_pt-br.json")
DB_ROOT = Path("data/spider/test_database")

RESULTS_DIR = Path("results")
PREDICTIONS_DIR = Path("predictions")

RESULTS_DIR.mkdir(exist_ok=True)
PREDICTIONS_DIR.mkdir(exist_ok=True)

MODEL_FILE_NAME = MODEL.replace(":", "-")

RESULT_FILE = RESULTS_DIR / f"{MODEL_FILE_NAME}.jsonl"
PREDICTION_FILE = PREDICTIONS_DIR / f"{MODEL_FILE_NAME}.txt"

# Carrega dataset
with DATASET_FILE.open(encoding="utf-8") as f:
    dataset = json.load(f)

assert len(dataset) == 2147

if TEST_LIMIT is not None:
    dataset = dataset[:TEST_LIMIT]


# Carrega resultados anteriores para permitir retomada
results = {}

if RESULT_FILE.exists():
    with RESULT_FILE.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                result = json.loads(line)
                results[result["index"]] = result


progress = tqdm(
    total=len(dataset),
    initial=len(results),
    desc=MODEL,
    unit="query",
)


for index, item in enumerate(dataset):

    # Já processado anteriormente
    if index in results:
        continue

    db_id = item["db_id"]
    db_path = DB_ROOT / db_id / f"{db_id}.sqlite"

    schema = get_schema(str(db_path))
    prompt = create_prompt(schema, item["question"])

    start = time.perf_counter()

    try:
        response = generate(MODEL, prompt)

        raw = response["response"]
        sql = clean_sql(raw)

        result = {
            "index": index,
            "db_id": db_id,
            "question": item["question"],
            "gold_sql": item["query"],
            "raw_response": raw,
            "generated_sql": sql,
            "wall_time": time.perf_counter() - start,
            "total_duration": response.get("total_duration"),
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
            "error": None,
        }

    except Exception as error:
        result = {
            "index": index,
            "db_id": db_id,
            "question": item["question"],
            "gold_sql": item["query"],
            "raw_response": "",
            "generated_sql": "",
            "wall_time": time.perf_counter() - start,
            "error": str(error),
        }

        tqdm.write(f"Erro no índice {index}: {error}")


    # Salva imediatamente
    with RESULT_FILE.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(result, ensure_ascii=False)
            + "\n"
        )

    results[index] = result

    progress.update(1)
    progress.set_postfix(
        db=db_id,
        last=f"{result['wall_time']:.1f}s"
    )


progress.close()


# Gera arquivo para o avaliador Spider
with PREDICTION_FILE.open("w", encoding="utf-8") as f:
    for index in range(len(dataset)):
        sql = results.get(
            index,
            {}
        ).get(
            "generated_sql",
            ""
        )

        # Uma consulta por linha
        sql = sql.replace("\n", " ").strip()

        f.write(sql + "\n")


print()
print("Execução concluída.")
print("Resultados:", RESULT_FILE)
print("Predictions:", PREDICTION_FILE)