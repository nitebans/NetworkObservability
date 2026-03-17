import requests

PROM_QUERY_URL = "http://localhost:9090/api/v1/query"
OLLAMA_URL = "http://localhost:11434/api/generate"

def detect_metric(question):
    q = question.lower()

    if "smf" in q and "session" in q:
        return "smf_active_sessions"

    return None


def ask_llm(prompt):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False
        }
    )

    return r.json()["response"]


while True:

    question = input("\nAsk AI: ")

    metric = detect_metric(question)

    if not metric:
        print("I could not determine which metric you want.")
        continue

    print("Metric selected:", metric)

    r = requests.get(PROM_QUERY_URL, params={"query": metric})
    result = r.json()

    if not result["data"]["result"]:
        print("No data found.")
        continue

    value = result["data"]["result"][0]["value"][1]
    
    print(f"\nCurrent {metric}: {value}\n")
    
    prompt = f"""
The Prometheus metric {metric} currently has value {value}.
Explain what this means in a telecom 5G core network.
"""

    explanation = ask_llm(prompt)

    print("\nAI Explanation:\n")
    print(explanation)
