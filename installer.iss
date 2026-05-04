[Setup]
AppName=Nihongo Master
AppVersion={#MyAppVersion}
AppPublisher=rapoyrazoglu
AppPublisherURL=https://github.com/rapoyrazoglu/nihongo
AppSupportURL=https://github.com/rapoyrazoglu/nihongo/issues
DefaultDirName={autopf}\Nihongo Master
DefaultGroupName=Nihongo Master
OutputBaseFilename=nihongo-setup-{#MyAppVersion}
SetupIconFile=assets\nihongo.ico
UninstallDisplayIcon={app}\nihongo.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Files]
Source: "nihongo-windows.exe"; DestDir: "{app}"; DestName: "nihongo.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\Nihongo Master"; Filename: "{app}\nihongo.exe"; IconFilename: "{app}\nihongo.exe"
Name: "{group}\Uninstall Nihongo Master"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Nihongo Master"; Filename: "{app}\nihongo.exe"; IconFilename: "{app}\nihongo.exe"; Tasks: desktopicon

[CustomMessages]
english.AdditionalOpts=Additional options:
english.AudioGroup=Audio:
english.DesktopShortcutDesc=Create a desktop shortcut
english.AddToPathDesc=Add to PATH (use nihongo from terminal)
english.AudioPackDesc=Download offline audio pack (~14 MB)

turkish.AdditionalOpts=Ek secenekler:
turkish.AudioGroup=Ses:
turkish.DesktopShortcutDesc=Masaustunde kisayol olustur
turkish.AddToPathDesc=PATH'e ekle (nihongo komutunu terminalden kullan)
turkish.AudioPackDesc=Cevrimdisi ses paketini indir (~14 MB)

german.AdditionalOpts=Zusaetzliche Optionen:
german.AudioGroup=Audio:
german.DesktopShortcutDesc=Desktop-Verknuepfung erstellen
german.AddToPathDesc=Zum PATH hinzufuegen (nihongo im Terminal nutzen)
german.AudioPackDesc=Offline-Audiopaket herunterladen (~14 MB)

french.AdditionalOpts=Options supplementaires :
french.AudioGroup=Audio :
french.DesktopShortcutDesc=Creer un raccourci sur le bureau
french.AddToPathDesc=Ajouter au PATH (utiliser nihongo dans le terminal)
french.AudioPackDesc=Telecharger le pack audio hors-ligne (~14 Mo)

spanish.AdditionalOpts=Opciones adicionales:
spanish.AudioGroup=Audio:
spanish.DesktopShortcutDesc=Crear acceso directo en el escritorio
spanish.AddToPathDesc=Anadir al PATH (usar nihongo desde la terminal)
spanish.AudioPackDesc=Descargar paquete de audio offline (~14 MB)

portuguese.AdditionalOpts=Opcoes adicionais:
portuguese.AudioGroup=Audio:
portuguese.DesktopShortcutDesc=Criar atalho na area de trabalho
portuguese.AddToPathDesc=Adicionar ao PATH (usar nihongo no terminal)
portuguese.AudioPackDesc=Baixar pacote de audio offline (~14 MB)

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcutDesc}"; GroupDescription: "{cm:AdditionalOpts}"
Name: "addtopath"; Description: "{cm:AddToPathDesc}"; GroupDescription: "{cm:AdditionalOpts}"; Flags: checkedonce
Name: "audiopack"; Description: "{cm:AudioPackDesc}"; GroupDescription: "{cm:AudioGroup}"; Flags: checkedonce

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$d = Join-Path $env:APPDATA 'nihongo\tts_cache'; New-Item -ItemType Directory -Force -Path $d | Out-Null; $zip = Join-Path $env:TEMP 'tts_cache.zip'; try {{ Invoke-WebRequest -Uri 'https://github.com/rapoyrazoglu/nihongo/releases/latest/download/tts_cache.zip' -OutFile $zip -UseBasicParsing; Expand-Archive -Path $zip -DestinationPath $d -Force; Remove-Item $zip -Force }} catch {{ }}"""; Description: "Downloading audio pack..."; StatusMsg: "Downloading offline audio pack..."; Tasks: audiopack; Flags: runhidden
Filename: "{app}\nihongo.exe"; Description: "Launch Nihongo Master"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
