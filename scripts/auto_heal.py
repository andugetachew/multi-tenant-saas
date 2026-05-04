# scripts/auto_heal.py
import requests
import subprocess
import time


def check_health():
    try:
        response = requests.get("http://localhost:8000/health/", timeout=10)
        return response.status_code == 200
    except:
        return False


def restart_services():
    subprocess.run(["docker-compose", "restart", "web"])
    subprocess.run(["docker-compose", "restart", "celery"])
    print("Services restarted")


def main():
    if not check_health():
        print(f"Health check failed at {time.time()}")
        restart_services()
        # Wait and check again
        time.sleep(30)
        if not check_health():
            print("CRITICAL: Services still down!")
            # Send alert
            subprocess.run(["python", "scripts/send_alert.py"])


if __name__ == "__main__":
    main()
