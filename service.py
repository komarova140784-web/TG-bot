import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import subprocess

class PythonService(win32service.Win32Service):
    _svc_name_ = "MonitorService"
    _svc_display_name_ = "Monitor Service"
    _svc_description_ = "Мониторинг компьютера"

    def __init__(self, args):
        win32service.Win32Service.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                             servicemanager.PYS_SERVICE_STARTED,
                             (self._svc_name_, ''))
        self.process = subprocess.Popen(['python', 'monitor.py'])
        self.process2 = subprocess.Popen(['python', 'watcher.py'])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.process.terminate()
        self.process2.terminate()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(PythonService)
