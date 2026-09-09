Get-Process python3.13 -ErrorAction SilentlyContinue | ForEach-Object {
    $p = $_
    try {
        $rect = New-Object System.Drawing.Rectangle
        $h = $p.MainWindowHandle
        if ($h -ne 0) {
            $ok = [System.Drawing.Rectangle]::new(0,0,0,0)
            $p.MainWindowTitle
        }
    } catch {}
}
