$WshShell = New-Object -comObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Golf Modeling Suite.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "c:\Users\diete\AppData\Local\Programs\Python\Python313\python.exe"
$Shortcut.Arguments = "c:\Users\diete\Repositories\Golf_Modeling_Suite\launchers\golf_launcher.py"
$Shortcut.WorkingDirectory = "c:\Users\diete\Repositories\Golf_Modeling_Suite"
$Shortcut.Description = "Launch the Golf Modeling Suite"
$Shortcut.IconLocation = "c:\Users\diete\Repositories\Golf_Modeling_Suite\launchers\assets\golf_icon.ico"
$Shortcut.Save()
Write-Host "Shortcut created at $ShortcutPath"
