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
Name: "{autodesktop}\Nihongo Master"; Filename: "{app}\nihongo.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional options:"
Name: "addtopath"; Description: "Add to PATH (use nihongo from terminal)"; GroupDescription: "Additional options:"; Flags: checkedonce

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Run]
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
