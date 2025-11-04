import time
import random
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# --- Configuration ---
# Set the URL for the Prometheus Pushgateway (Team Member 2's domain)
PUSHGATEWAY_URL = 'http://54.82.105.142:9091'  # Update this to your deployed URL
JOB_NAME = 'water_sensor_simulator'
HOUSEHOLDS = {
    'A101': 'NORMAL',        # Normal usage pattern
    'B202': 'SLOW_LEAK',     # Simulating a toilet or faucet leak
    'C303': 'MAJOR_LEAK'     # Simulating a burst pipe or hose left on
}
UPDATE_INTERVAL_SECONDS = 15

# --- Metrics Setup ---
# Create a new registry for the metrics
registry = CollectorRegistry()

# Define the Gauge metric for water flow rate
# The labels 'household' and 'mode' allow us to track metrics per simulated entity
WATER_FLOW_RATE = Gauge(
    'household_water_flow_rate_lpm',
    'Current water flow rate in liters per minute (LPM).',
    ['household', 'mode'],
    registry=registry
)

def generate_normal_flow(hour):
    """Simulates typical household water usage patterns."""
    # Peak usage hours (6-9 AM, 6-9 PM)
    if 6 <= hour <= 9 or 18 <= hour <= 21:
        # High chance of flow (1-10 LPM for a short duration)
        if random.random() < 0.4:
            return round(random.uniform(1.0, 10.0), 2)
        else:
            return 0.0
    # Low usage hours
    elif 10 <= hour <= 17:
        # Low chance of flow (0-5 LPM)
        if random.random() < 0.1:
            return round(random.uniform(0.5, 5.0), 2)
        else:
            return 0.0
    # Overnight (10 PM - 5 AM) - almost always zero
    else:
        return 0.0

def generate_leak_flow(leak_type):
    """Simulates a continuous leak."""
    if leak_type == 'SLOW_LEAK':
        # Constant, low flow (e.g., dripping faucet)
        return round(random.uniform(0.05, 0.2), 2)
    elif leak_type == 'MAJOR_LEAK':
        # Constant, high flow (e.g., burst pipe)
        return round(random.uniform(3.0, 8.0), 2)
    return 0.0

def push_metrics():
    """Generates the metrics and pushes them to the Pushgateway."""
    current_hour = time.localtime().tm_hour
    print(f"\n--- Pushing Metrics at {time.strftime('%H:%M:%S')} ---")

    for household, mode in HOUSEHOLDS.items():
        flow = 0.0

        if mode == 'NORMAL':
            flow = generate_normal_flow(current_hour)
        elif mode in ['SLOW_LEAK', 'MAJOR_LEAK']:
            flow = generate_leak_flow(mode)

        # Set the gauge value
        WATER_FLOW_RATE.labels(household=household, mode=mode).set(flow)

        print(f"  {household} ({mode}): {flow:.2f} LPM")

    try:
        # Push all collected metrics in the registry to the Pushgateway
        push_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry)
        print("Push successful.")
    except Exception as e:
        print(f"Failed to push metrics to Pushgateway at {PUSHGATEWAY_URL}. Error: {e}")
        print("Please ensure the Pushgateway service is running.")

# --- Main Loop ---
if __name__ == '__main__':
    print(f"Starting Water Sensor Simulator. Pushing to: {PUSHGATEWAY_URL}")
    print(f"Households running: {HOUSEHOLDS}")
    print("Press Ctrl+C to stop.")
    
    while True:
        push_metrics()
        time.sleep(UPDATE_INTERVAL_SECONDS)