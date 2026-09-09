Get-WmiObject Win32_Process -Filter "Name='python3.13.exe'" | Select-Object ProcessId, CommandLine
