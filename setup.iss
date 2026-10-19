; HD Launcher Windows Setup - Inno Setup 6
; Compiler input: dist\HDLauncher\HDLauncher.exe and its _internal directory
; Per-user installation: no Administrator permission required.

#define ProductName "HD Launcher"
#define ProductVersion "1.7.0"
#define ProductPublisher "HD Games"
#define ProductExe "HDLauncher.exe"

[Setup]
AppId={{9D3D494F-DA56-445C-80E2-B47A9B334816}
AppName={#ProductName}
AppVersion={#ProductVersion}
AppVerName={#ProductName} {#ProductVersion}
AppPublisher={#ProductPublisher}
DefaultDirName={localappdata}\Programs\HDLauncher
DefaultGroupName=HD Launcher
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
DisableProgramGroupPage=yes
UninstallDisplayName=HD Launcher
UninstallDisplayIcon={app}\{#ProductExe}
SetupIconFile=assets\hd-launcher.ico
WizardStyle=modern
WizardImageFile=installer\wizard-side.bmp
WizardSmallImageFile=installer\wizard-small.bmp
OutputDir=installer-output
OutputBaseFilename=HDLauncher-Setup-v{#ProductVersion}
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
VersionInfoVersion={#ProductVersion}
VersionInfoProductName={#ProductName}
VersionInfoDescription=Instalador do HD Launcher para Windows
VersionInfoCompany={#ProductPublisher}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "dist\HDLauncher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\HD Launcher"; Filename: "{app}\{#ProductExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\HD Launcher"; Filename: "{app}\{#ProductExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ProductExe}"; Description: "Abrir o HD Launcher"; Flags: nowait postinstall skipifsilent
; When the updater installs silently, reopen the new HD Launcher automatically.
Filename: "{app}\{#ProductExe}"; Flags: nowait skipifnotsilent

; Nenhuma linha [UninstallDelete] apaga contas, bibliotecas ou jogos pessoais.
; Os dados permanecem em %APPDATA%\HDLauncher\accounts.db.
