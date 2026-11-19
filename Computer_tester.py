import platform
import socket
import sys

try:
    import psutil
except ImportError:
    sys.exit("Missing dependency. Install it with: python -m pip install psutil")


def report(label, status, detail):
    print(f"[{status}] {label}: {detail}")


def check_computer():
    print(f"Computer check — {platform.system()} {platform.release()}")
    print(f"Processor: {platform.processor() or 'Not reported by system'}")
    print(
        f"CPU cores: {psutil.cpu_count(logical=False) or 'Unknown'} physical, "
        f"{psutil.cpu_count(logical=True) or 'Unknown'} logical"
    )

    # This measures current activity; it is not a CPU stress test.
    cpu_percent = psutil.cpu_percent(interval=1)
    report(
        "CPU activity",
        "INFO" if cpu_percent < 90 else "WARN",
        f"{cpu_percent:.1f}% during a 1-second sample",
    )

    memory = psutil.virtual_memory()
    report(
        "Memory",
        "WARN" if memory.percent >= 90 else "OK",
        f"{memory.percent:.1f}% used; "
        f"{memory.available / (1024 ** 3):.1f} GiB available",
    )

    print("\nDisk space:")
    seen_mounts = set()
    for partition in psutil.disk_partitions(all=False):
        if partition.mountpoint in seen_mounts:
            continue
        seen_mounts.add(partition.mountpoint)

        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (PermissionError, OSError):
            report(partition.mountpoint, "INFO", "Could not read usage")
            continue

        report(
            partition.mountpoint,
            "WARN" if usage.percent >= 90 else "OK",
            f"{usage.percent:.1f}% used; "
            f"{usage.free / (1024 ** 3):.1f} GiB free",
        )

    print("\nNetwork:")
    try:
        socket.getaddrinfo("example.com", 443)
        report("DNS lookup", "OK", "example.com resolved")
    except OSError as error:
        report("DNS lookup", "WARN", str(error))

    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=3):
            report("Internet connection", "OK", "Connected to 1.1.1.1 on port 443")
    except OSError as error:
        report("Internet connection", "WARN", str(error))

    battery = psutil.sensors_battery()
    if battery is not None:
        state = "charging" if battery.power_plugged else "not charging"
        report("Battery", "INFO", f"{battery.percent:.0f}% ({state})")
    else:
        report("Battery", "INFO", "No battery information available")

    # Temperature sensors aren't available on every computer or OS.
    try:
        temperatures = psutil.sensors_temperatures()
        readings = [
            (name, sensor.label or sensor.name, sensor.current)
            for name, sensors in temperatures.items()
            for sensor in sensors
            if sensor.current is not None
        ]

        if readings:
            print("\nTemperature readings (informational):")
            for name, label, value in readings:
                print(f"  {label} ({name}): {value:.1f} °C")
        else:
            report("Temperature sensors", "INFO", "No readings available")
    except (AttributeError, OSError):
        report("Temperature sensors", "INFO", "Not supported on this system")


if __name__ == "__main__":
    check_computer()
