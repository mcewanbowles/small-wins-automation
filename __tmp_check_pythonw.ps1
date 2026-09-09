Get-WmiObject Win32_Process -Filter "Name='pythonw3.13.exe'" | Select-Object ProcessId, CommandLine
