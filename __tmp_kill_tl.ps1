Get-Process python3.13,cmd -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Id -notin 24596,9356) {
        try { Stop-Process -Id $_.Id -Force } catch {}
    }
}
