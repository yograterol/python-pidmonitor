from ctrldaemon import ControlDaemon
from pidmonitor.pidmonitor import PidMonitor

if __name__ == "__main__":
    pid_monitor = PidMonitor()
    pid_monitor.activate_thread()
