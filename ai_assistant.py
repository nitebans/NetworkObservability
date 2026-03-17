import requests
import time

PROM_QUERY_URL = "http://localhost:9090/api/v1/query"
PROM_RANGE_URL = "http://localhost:9090/api/v1/query_range"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Metric catalog for LLM selection
METRIC_CATALOG = {
    "smf_active_sessions": "number of active SMF sessions in 5G core",
    "node_cpu_seconds_total": "CPU utilization",
    "node_memory_MemAvailable_bytes": "available system memory"
}


def ask_llm(prompt):

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False
        }
    )

    return r.json()["response"].strip()


def choose_metric(question):

    catalog_text = "\n".join(
        [f"{k}: {v}" for k, v in METRIC_CATALOG.items()]
    )

    prompt = f"""
You are a telecom network observability assistant.

User question:
{question}

Available metrics:
{catalog_text}

Return ONLY the metric name that answers the question.
"""

    response = ask_llm(prompt)

    for metric in METRIC_CATALOG:
        if metric in response:
            return metric

    return None


def get_current_value(metric):

    r = requests.get(PROM_QUERY_URL, params={"query": metric})

    data = r.json()["data"]["result"]

    if not data:
        return None

    return float(data[0]["value"][1])


def get_trend(metric):

    end = int(time.time())
    start = end - 300

    params = {
        "query": metric,
        "start": start,
        "end": end,
        "step": 30
    }

    r = requests.get(PROM_RANGE_URL, params=params)

    data = r.json()["data"]["result"]

    if not data:
        return "unknown"

    values = data[0]["values"]

    first = float(values[0][1])
    last = float(values[-1][1])

    if last > first:
        return "increasing"
    elif last < first:
        return "decreasing"
    else:
        return "stable"


while True:

    question = input("\nAsk AI: ")

    metric = choose_metric(question)

    if not metric:
        print("Could not determine metric.")
        continue

    print("\nMetric selected:", metric)

    value = get_current_value(metric)

    if value is None:
        print("No data found.")
        continue

    trend = get_trend(metric)

    print(f"Current {metric}: {value}")
    print(f"Trend (last 5 minutes): {trend}")

    explain_prompt = f"""
Metric {metric} currently has value {value}.
The trend in the last 5 minutes is {trend}.

Explain what this means in a telecom 5G core network.
"""

    explanation = ask_llm(explain_prompt)

    print("\nAI Explanation:\n")
    print(explanation)
