$sh = (New-Object -ComObject WScript.Shell).CreateShortcut('C:\Users\mcewa\Desktop\Tool Launcher.lnk')
Write-Output ('Target: ' + $sh.TargetPath)
Write-Output ('Args: ' + $sh.Arguments)
Write-Output ('Work: ' + $sh.WorkingDirectory)
