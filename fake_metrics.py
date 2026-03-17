from prometheus_client import start_http_server, Gauge
import random
import time

smf_sessions = Gauge('smf_active_sessions', 'Active SMF Sessions')

start_http_server(8000)

while True:
    smf_sessions.set(random.randint(1000,2000))
    time.sleep(60)
