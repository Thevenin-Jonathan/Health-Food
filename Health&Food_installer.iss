
; Script généré par le script de build de Health&Food
; Inno Setup Script

#define MyAppName "Health&Food"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Warzonefury"
#define MyAppExeName "Health&Food.exe"

[Setup]
; NOTE: La valeur AppId est unique pour cette application.
; Ne pas utiliser la même valeur AppId dans d'autres installateurs.
AppId={{98761ABC-01FE-4D61-9E22-C17331AA6123}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
LicenseFile="LICENSE"
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Si vous souhaitez que l'installateur requiert des privilèges administrateur
; décommenter la ligne suivante:
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=Health&Food-setup-1.0.1
SetupIconFile=src/ui/icons/app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Options pour la gestion des mises à jour
AppMutex=HealthAndFoodAppMutex
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll
RestartApplications=no
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#AppVersion}
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist/Health&Food\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Dirs]
Name: "{userappdata}\{#MyAppName}\data"; Permissions: users-full

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
