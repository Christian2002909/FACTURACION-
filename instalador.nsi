; NSIS Installer Script para FACTURACION- (Paraguay)
; Instala la aplicación en Windows con acceso directo y desinstalador

!include "MUI2.nsh"
!include "x64.nsh"

; Configuración General
Name "Sistema de Facturación Paraguay"
OutFile "dist\FACTURACION-setup.exe"
InstallDir "$PROGRAMFILES\FACTURACION"
ShowInstDetails show
ShowUninstDetails show

; Variables
Var StartMenuFolder

; Interfaz
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU "Application" $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "Spanish"

; Sección de Instalación
Section "Instalar FACTURACION"
  SetOutPath "$INSTDIR"

  ; Copiar archivos (después de PyInstaller)
  File /r "dist\FACTURACION\*.*"

  ; Crear carpetas de datos
  CreateDirectory "$APPDATA\FACTURACION\data\facturas"
  CreateDirectory "$APPDATA\FACTURACION\data\certificados"
  CreateDirectory "$APPDATA\FACTURACION\data\backups"

  ; Crear acceso directo en Inicio
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\FACTURACION.lnk" "$INSTDIR\FACTURACION.exe" "" "$INSTDIR\FACTURACION.exe" 0
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Desinstalar.lnk" "$INSTDIR\uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END

  ; Crear acceso directo en Escritorio
  CreateShortcut "$DESKTOP\FACTURACION.lnk" "$INSTDIR\FACTURACION.exe" "" "$INSTDIR\FACTURACION.exe" 0

  ; Crear entrada en Agregar/Quitar Programas
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FACTURACION" "DisplayName" "Sistema de Facturación Paraguay"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FACTURACION" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FACTURACION" "DisplayVersion" "1.0.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FACTURACION" "Publisher" "Tu Nombre"

  ; Crear desinstalador
  WriteUninstaller "$INSTDIR\uninstall.exe"

  DetailPrint "Instalación completada exitosamente"
SectionEnd

; Sección de Desinstalación
Section "Uninstall"
  ; Eliminar accesos directos
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  RMDir /r "$SMPROGRAMS\$StartMenuFolder"
  Delete "$DESKTOP\FACTURACION.lnk"

  ; Eliminar archivos de programa (PERO NO datos del usuario)
  RMDir /r "$INSTDIR"

  ; Eliminar entrada del registro
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FACTURACION"

  DetailPrint "Desinstalación completada"
SectionEnd
