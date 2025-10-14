Set WshShell = WScript.CreateObject("WScript.Shell")
WshShell.Run "cmd /c start /B  python watcher.py", 0, false
