Set shell = CreateObject("WScript.Shell")
pasta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

shell.CurrentDirectory = pasta
shell.Run "cmd /c python ""servidor(4)_corrigido_v2.py""", 0, False
