#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppName=KeyTik
AppVersion={#AppVersion}
AppPublisher=Fajar Rahmad Jaya
AppPublisherURL=https://keytik.com
AppId=2c7a0ac8-ce1e-4799-8000-3dbe16bac52e
DefaultDirName={commonpf}\KeyTik
DefaultGroupName=KeyTik
SourceDir=.\dist\KeyTik v{#AppVersion}
OutputDir=..
OutputBaseFilename=KeyTik v{#AppVersion} Installer
SetupIconFile=_internal\Data\icon.ico
UninstallDisplayIcon=_internal\Data\icon.ico
UninstallDisplayName=KeyTik
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
CreateUninstallRegKey=yes
UninstallFilesDir={app}\uninstall
UpdateUninstallLogAppName=yes
AppMutex=KeyTikMutex
UsePreviousAppDir=yes
DirExistsWarning=no
LicenseFile=LICENSE

[Files]
Source: "*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Registry]
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\KeyTik.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\KeyTik.exe"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\KeyTik.exe"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Classes\Applications\KeyTik.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "KeyTik"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Classes\Applications\KeyTik.exe\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icon.ico"; Flags: uninsdeletekey

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Icons]
Name: "{group}\KeyTik"; Filename: "{app}\KeyTik.exe"; IconFilename: "_internal\Data\icon.ico"
Name: "{group}\Uninstall KeyTik"; Filename: "{uninstallexe}"
Name: "{commondesktop}\KeyTik"; Filename: "{app}\KeyTik.exe"; IconFilename: "_internal\Data\icon.ico"; Tasks: desktopicon

[InstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{commonpf}\KeyTik"
Type: filesandordirs; Name: "{commonpf32}\KeyTik"

[UninstallDelete]
Type: files; Name: "{app}\*.*"
Type: dirifempty; Name: "{app}"
Type: filesandordirs; Name: "{app}\uninstall"

[Code]
var
  AHKCheckBox: TCheckBox;
  InterceptionCheckBox: TCheckBox;
  DownloadPage: TDownloadWizardPage;
  NeedsRestart: Boolean;
  RunAppCheckBox: TNewCheckBox;

function IsInterceptionInstalled: Boolean;
begin
  Result := FileExists(ExpandConstant('C:\Windows\System32\drivers\keyboard.sys'))
end;

function IsAHKInstalled: Boolean;
begin
  Result := DirExists('C:\Program Files\AutoHotkey\v2');
end;

procedure InitializeWizard;
var
  ComponentsLabel: TLabel;
  ComponentsPage: TWizardPage;
begin
  ComponentsPage := CreateCustomPage(wpLicense, 'Third-party Components',
    'Select additional components to install');

  ComponentsLabel := TLabel.Create(ComponentsPage);
  ComponentsLabel.Parent := ComponentsPage.Surface;
  ComponentsLabel.Top := ScaleY(8);
  ComponentsLabel.Caption := 'The following components are required for certain features:';
  ComponentsLabel.Width := ComponentsPage.SurfaceWidth;

  AHKCheckBox := TCheckBox.Create(ComponentsPage);
  AHKCheckBox.Parent := ComponentsPage.Surface;
  AHKCheckBox.Top := ComponentsLabel.Top + ComponentsLabel.Height + ScaleY(12);
  AHKCheckBox.Caption := 'Install AutoHotkey v2 (Required)';
  AHKCheckBox.Width := ComponentsPage.SurfaceWidth;
  AHKCheckBox.Checked := True; // Checked by default

  InterceptionCheckBox := TCheckBox.Create(ComponentsPage);
  InterceptionCheckBox.Parent := ComponentsPage.Surface;
  InterceptionCheckBox.Top := AHKCheckBox.Top + AHKCheckBox.Height + ScaleY(8);
  InterceptionCheckBox.Caption := 'Install Interception Driver (Optional)';
  InterceptionCheckBox.Width := ComponentsPage.SurfaceWidth;

  if IsInterceptionInstalled then
  begin
    InterceptionCheckBox.Checked := False;
    InterceptionCheckBox.Enabled := False;
    InterceptionCheckBox.Caption := InterceptionCheckBox.Caption + ' Installed';
  end;

  if IsAHKInstalled then
  begin
    AHKCheckBox.Checked := False;
    AHKCheckBox.Enabled := False;
    AHKCheckBox.Caption := AHKCheckBox.Caption + ' Installed';
  end;

  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing),
    SetupMessage(msgPreparingDesc), nil);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    if not Assigned(RunAppCheckBox) then
    begin
      RunAppCheckBox := TNewCheckBox.Create(WizardForm);
      RunAppCheckBox.Parent := WizardForm.FinishedPage;
      RunAppCheckBox.Caption := 'Run KeyTik';
      RunAppCheckBox.Checked := True;
      RunAppCheckBox.Left := WizardForm.FinishedLabel.Left;
      RunAppCheckBox.Top := WizardForm.FinishedLabel.Top + WizardForm.FinishedLabel.Height + ScaleY(16);
      RunAppCheckBox.Width := WizardForm.FinishedPage.Width - 2 * RunAppCheckBox.Left;
    end;
    RunAppCheckBox.Visible := True;
  end
  else if Assigned(RunAppCheckBox) then
    RunAppCheckBox.Visible := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  BatPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    if InterceptionCheckBox.Checked then
    begin
      BatPath := ExpandConstant('{app}\_internal\data\inter_install.bat');
      if FileExists(BatPath) then
      begin
        if ShellExec('', BatPath, '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
        begin
          NeedsRestart := True;
        end
        else
        begin
          MsgBox('Failed to run Interception installer: ' + BatPath, mbError, MB_OK);
        end;
      end
      else
      begin
        MsgBox('Interception installer not found: ' + BatPath, mbError, MB_OK);
      end;
    end;

    if AHKCheckBox.Checked then
    begin
      BatPath := ExpandConstant('{app}\_internal\data\ahk_install.bat');
      if FileExists(BatPath) then
      begin
        if not ShellExec('', BatPath, '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
        begin
          MsgBox('Failed to run AutoHotkey installer: ' + BatPath, mbError, MB_OK);
        end;
      end
      else
      begin
        MsgBox('AutoHotkey installer not found: ' + BatPath, mbError, MB_OK);
      end;
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  AppPath: string;
  ResultCode: Integer;
begin
  Result := True;
  if (CurPageID = wpFinished) and Assigned(RunAppCheckBox) and RunAppCheckBox.Checked then
  begin
    AppPath := ExpandConstant('{app}\KeyTik.exe');
    if FileExists(AppPath) then
      ShellExec('', AppPath, '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
  end;
end;

[Messages]
FinishedLabel=Setup has completed installing [name] on your computer.%n%nIf you installed the Interception driver, you must restart your computer to complete the installation.
