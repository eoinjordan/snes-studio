#define MyAppName "SNES Studio"
#define MyAppVersion GetEnv("SNES_STUDIO_VERSION")
#define MyAppPublisher "SNES Studio"
#define MyAppExeName "SNES Studio.exe"
#define MyCliExeName "snes-studio.exe"

[Setup]
AppId={{A850A1A8-5D43-47B8-9239-8BB8869056CC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SNES Studio
DefaultGroupName=SNES Studio
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=SNES-Studio-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "modifypath"; Description: "Add snes-studio to PATH"; GroupDescription: "Additional tasks:"

[Files]
Source: "..\..\build\windows\payload\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SNES Studio"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\SNES Studio CLI"; Filename: "{app}\{#MyCliExeName}"
Name: "{autodesktop}\SNES Studio"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SNES Studio"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  CurrentPath: string;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('modifypath') then
  begin
    if RegQueryStringValue(HKCU, 'Environment', 'Path', CurrentPath) then
    begin
      if Pos(ExpandConstant('{app}'), CurrentPath) = 0 then
      begin
        CurrentPath := CurrentPath + ';' + ExpandConstant('{app}');
        RegWriteStringValue(HKCU, 'Environment', 'Path', CurrentPath);
      end;
    end
    else
      RegWriteStringValue(HKCU, 'Environment', 'Path', ExpandConstant('{app}'));
  end;
end;
