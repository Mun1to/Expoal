; Inno Setup script para Expoal.
; Compilar: & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\expoal.iss
; Genera dist\Expoal-<version>-setup.exe a partir de dist\Expoal (build de PyInstaller).

#define MyAppName "Expoal"
; La versión puede inyectarse desde la línea de comandos: ISCC /DMyAppVersion=1.2.3
#ifndef MyAppVersion
  #define MyAppVersion "1.1.0"
#endif
#define MyAppPublisher "Munir Torres"
#define MyAppURL "https://mun1to.github.io/Expoal/"
#define MyAppExeName "Expoal.exe"

[Setup]
; AppId identifica la app para actualizaciones y desinstalación. No cambiar entre versiones.
AppId={{5C015696-9505-48F5-9E16-E45F0FECE5EA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\dist
OutputBaseFilename=Expoal-{#MyAppVersion}-setup
SetupIconFile=..\assets\expoal.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Instala sin pedir administrador (en la carpeta del usuario) pero permite elegir para todos.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
; Auto-update: si Expoal está corriendo, ciérralo antes de instalar (detección por mutex).
CloseApplications=yes
RestartApplications=no
AppMutex=ExpoalRunningMutex

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Expoal\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Instalación interactiva: casilla "Ejecutar Expoal" al terminar.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
; Actualización silenciosa (auto-update): reabre Expoal automáticamente.
Filename: "{app}\{#MyAppExeName}"; Flags: nowait; Check: WizardSilent
