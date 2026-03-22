#!/usr/bin/env python3
"""
Master Automated Test Runner
Runs complete test with config update, container restart, and data capture
"""

import subprocess
import time
import sys
import os
import yaml


def update_go2rtc_config(config_params):
    """Update iphone_cam stream with new ffmpeg configuration"""

#     config_path = "C:/Home-Assistant-RTSP-Server/software/deployment/camera-streaming/go2rtc/config/go2rtc.yaml"
    config_path = "/home/aiot/Documents/Containers/networking/homeassistant/go2rtc/config/go2rtc.yml"

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}

    if 'streams' not in config:
        config['streams'] = {}

    # Update camera with test parameters
    config['streams']['Camera_3'] = [
         f"ffmpeg:rtsp://admin:aiot2024@192.168.50.13:554/h264Preview_01_main#video={config_params['codec']}#hardware=cuda#width={config_params['width']}#height={config_params['height']}#bitrate={config_params['bitrate']}#framerate={config_params['framerate']}"
    ]

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(
        f"✓ Updated iphone_cam: {config_params['codec']}, {config_params['width']}x{config_params['height']}, {config_params['bitrate']}, {config_params['framerate']}fps")

def restart_container():
    """Restart Go2RTC container"""

    print("Restarting Go2RTC container...")
    result = subprocess.run(['podman', 'restart', 'go2rtc-ha'], capture_output=True)

    if result.returncode == 0:
        print("✓ Container restarted successfully")
        return True
    else:
        print(f"✗ Failed to restart container: {result.stderr.decode()}")
        return False

def trigger_stream():
    """Start consuming Go2RTC stream to force transcoding"""
    try:
        process = subprocess.Popen(
            ['ffmpeg', '-i', 'rtsp://localhost:8554/Camera_3',
             '-f', 'null', '-'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("  ✓ Stream consumer started")
        return process
    except Exception as e:
        print(f"  ✗ Failed to start consumer: {e}")
        return None

def wait_for_active_stream(timeout=60):
    """Wait until Go2RTC has an active producer stream"""
    print("\n  Waiting for active stream...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = subprocess.run(
                ['podman', 'logs', 'go2rtc', '--tail', '20'],
                capture_output=True, text=True, timeout=10
            )
            logs = result.stdout.lower() + result.stderr.lower()
            if 'start producer' in logs or 'run rtsp' in logs:
                print("  ✓ Active stream detected!")
                return True
            else:
                trigger_stream()
                time.sleep(5)
        except Exception as e:
            print(f"  Warning: {e}")
            time.sleep(5)
    print("  ✗ Stream not detected after timeout!")
    return False

def verify_data_capture():
    """Verify Go2RTC container is running and producing stats"""
    try:
        result = subprocess.run(
            ['podman', 'stats', '--no-stream', '--format',
             '{{.Name}},{{.CPUPerc}}'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'go2rtc' in line.lower():
                    cpu = float(line.split(',')[1].strip().replace('%', ''))
                    print(f"  ✓ Container active - CPU: {cpu:.1f}%")
                    return True
        print("  ✗ Container not found in stats!")
        return False
    except Exception as e:
        print(f"  ✗ Stats verification error: {e}")
        return False

def run_test(test_id, config_params, duration=60, stabilization_time=60):
    """Run complete automated test"""

    print("\n" + "="*80)
    print(f"RUNNING TEST: {test_id}")
    print("="*80)

    # Step 1: Update configuration
    print("\n[1/5] Updating configuration...")
    update_go2rtc_config(config_params)

    # Step 2: Restart container
    print("\n[2/5] Restarting container...")
    if not restart_container():
        print("✗ Test failed: Could not restart container")
        return False

    # Step 3: Wait for stabilization
    print(f"\n[3/5] Waiting {stabilization_time} seconds for stabilization...")
    for i in range(stabilization_time, 0, -1):
        print(f"\r  Stabilizing... {i} seconds remaining", end='', flush=True)
        time.sleep(1)
    print("\n✓ Stream stabilized")

    # Step 4: Start stream consumer
    print("\n[4/6] Starting stream consumer...")
    consumer = trigger_stream()
    time.sleep(5)  # give time to connect

    # Step 5: Capture performance data
    print(f"\n[5/6] Capturing performance data for {duration} seconds...")
    import capture_stats
    log_file = capture_stats.capture_docker_stats(test_id, duration)

    # Stop consumer after capture
    if consumer:
        consumer.terminate()
        print("  ✓ Stream consumer stopped")

    # Step 6: Cool down
    print("\n[6/6] Cooling down before next test...")
    time.sleep(10)

    print(f"\n✓ Test {test_id} completed successfully!")
    print(f"  Data saved to: {log_file}")

    return True

# Test configurations
TESTS = {
    #Group 1 h264 vs h265 codec comparisson
    'T1A': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '30'},
    'T1B': {'codec': 'h265', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '30'},

    #Group 2 resolution comparisson
    'T2A': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '30'},
    'T2B': {'codec': 'h264', 'width': '1280', 'height': '720',  'bitrate': '2000k', 'framerate': '30'},
    'T2C': {'codec': 'h264', 'width': '854',  'height': '480',  'bitrate': '2000k', 'framerate': '30'},

    #Group 3 bitrate comparisson
    'T3A': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '30'},
    'T3B': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '1000k', 'framerate': '30'},
    'T3C': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '500k',  'framerate': '30'},

    #Group 4 framerate comparisson
    'T4A': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '30'},
    'T4B': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '15'},
    'T4C': {'codec': 'h264', 'width': '1920', 'height': '1080', 'bitrate': '2000k', 'framerate': '10'},

    #Group 5 h265 codec with different resolution comparisson
    'T5A': {'codec': 'h265', 'width': '1280', 'height': '720',  'bitrate': '2000k', 'framerate': '30'},
    'T5B': {'codec': 'h265', 'width': '854',  'height': '480',  'bitrate': '2000k', 'framerate': '30'},

    #Group 6 h265 codec with different bitrate comparisson
    'T6A': {'codec': 'h265', 'width': '1920', 'height': '1080', 'bitrate': '1000k', 'framerate': '30'},
    'T6B': {'codec': 'h265', 'width': '1920', 'height': '1080', 'bitrate': '500k',  'framerate': '30'},
}

def main():
    """Run all tests automatically"""

    # Create directories
    os.makedirs('test_results/logs', exist_ok=True)

    if len(sys.argv) > 1:
        # Run specific test
        test_id = sys.argv[1]
        run_num = sys.argv[2] if len(sys.argv) > 2 else '1'

        if test_id not in TESTS:
            print(f"Unknown test: {test_id}")
            print(f"Available tests: {', '.join(TESTS.keys())}")
            return

        config = TESTS[test_id].copy()

        run_test(f'{test_id}_run{run_num}', config)
    else:
        # Run all tests
        print("="*80)
        print("AUTOMATED TEST SUITE - ALL TESTS")
        print("="*80)
        print(f"\nTotal tests to run: {len(TESTS) * 3} (11 configs × 3 runs)")
        print("\nThis will take approximately 2-3 hours.")
        input("\nPress Enter to start, or Ctrl+C to cancel...")

        for test_id, config in TESTS.items():
            for run_num in range(1, 4):  # 3 runs per config
                config_copy = config.copy()

                success = run_test(f'{test_id}_run{run_num}', config_copy)

                if not success:
                    print(f"\n✗ Test {test_id}_run{run_num} failed!")
                    choice = input("Continue with remaining tests? (y/n): ")
                    if choice.lower() != 'y':
                        break

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED!")
        print("="*80)
        print("\nNext step: Run 'python analyze_results.py' to generate charts")

if __name__ == "__main__":
    main()
