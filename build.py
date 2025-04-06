import os
import sys
import shutil
import subprocess
import argparse
import datetime
import traceback

# Configuration de base du projet
APP_NAME = "Health&Food"
APP_VERSION = (
    "1.0.0"  # À mettre à jour manuellement ou à extraire d'un fichier de configuration
)
MAIN_SCRIPT = "main.py"
ICON_PATH = "src/ui/icons/app_icon.ico"  # Ajustez selon l'emplacement de votre icône
OUTPUT_DIR = "dist"

# Dossiers à inclure dans la distribution
INCLUDE_DIRS = ["src"]

# Fichiers à inclure explicitement
INCLUDE_FILES = ["LICENSE"]

# Fichiers et dossiers à exclure
EXCLUDE_PATTERNS = ["__pycache__", "*.pyc", "*.pyo", "*.pyd", "build", "dist"]


def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} en exécutable")

    parser.add_argument(
        "--onefile", action="store_true", help="Créer un seul fichier exécutable"
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Afficher la console (window mode par défaut)",
    )
    parser.add_argument(
        "--icon", default=ICON_PATH, help="Chemin vers l'icône de l'application"
    )
    parser.add_argument("--name", default=APP_NAME, help="Nom de l'application")
    parser.add_argument(
        "--version", default=APP_VERSION, help="Version de l'application"
    )
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Dossier de sortie")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Nettoyer le dossier de build avant de démarrer",
    )
    parser.add_argument(
        "--upx",
        action="store_true",
        help="Utiliser UPX pour compresser l'exécutable (si installé)",
    )

    return parser.parse_args()


def clean_build_directories():
    """Nettoyer les dossiers de build et dist"""
    for directory in ["build", "dist"]:
        if os.path.exists(directory):
            print(f"Nettoyage du dossier {directory}...")
            try:
                shutil.rmtree(directory)
            except OSError as e:
                print(f"Erreur lors du nettoyage de {directory}: {e}")


def create_version_info(args):
    """Crée un fichier version.txt pour l'information de version Windows"""
    version_path = "version.txt"
    version_parts = args.version.split(".")

    # Ajuster pour garantir 4 parties (major.minor.patch.build)
    while len(version_parts) < 4:
        version_parts.append("0")

    # Limiter à 4 parties maximum
    version_parts = version_parts[:4]

    # Construire le contenu du fichier version
    version_content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({','.join(version_parts)}),
    prodvers=({','.join(version_parts)}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'{args.name}'),
        StringStruct(u'FileVersion', u'{args.version}'),
        StringStruct(u'InternalName', u'{args.name}'),
        StringStruct(u'LegalCopyright', u'Copyright © {datetime.datetime.now().year}'),
        StringStruct(u'OriginalFilename', u'{args.name}.exe'),
        StringStruct(u'ProductName', u'{args.name}'),
        StringStruct(u'ProductVersion', u'{args.version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

    with open(version_path, "w", encoding="utf-8") as f:
        f.write(version_content)

    return version_path


def build_executable(args):
    """Construit l'exécutable avec PyInstaller"""
    print(f"Création de l'exécutable {args.name} v{args.version}...")

    # Vérifier si l'icône existe
    if args.icon and not os.path.exists(args.icon):
        print(f"Attention: L'icône spécifiée n'existe pas: {args.icon}")
        args.icon = None

    # Créer les informations de version
    version_file = create_version_info(args)

    # Construire la commande PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        args.name,
        "--clean" if args.clean else "--noconfirm",
    ]

    # Ajouter les options en fonction des arguments
    if args.onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if not args.console:
        cmd.append("--windowed")

    if args.icon:
        cmd.extend(["--icon", args.icon])

    if args.upx:
        cmd.append("--upx-dir=.")  # Cherche UPX dans le répertoire courant

    # Ajouter les dossiers à inclure
    for directory in INCLUDE_DIRS:
        if os.path.exists(directory):
            for dirpath, dirnames, filenames in os.walk(directory):
                # Filtrer les dossiers exclus
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not any(excl in d for excl in EXCLUDE_PATTERNS)
                ]

                # Ajouter les dossiers Python comme packages
                if "__init__.py" in filenames:
                    package_path = os.path.relpath(dirpath, ".").replace(os.sep, ".")
                    cmd.extend(["--hidden-import", package_path])

                # Ajouter les fichiers de données
                for filename in filenames:
                    if not any(excl in filename for excl in EXCLUDE_PATTERNS):
                        filepath = os.path.join(dirpath, filename)
                        dest_path = os.path.dirname(os.path.relpath(filepath, "."))
                        cmd.extend(["--add-data", f"{filepath}{os.pathsep}{dest_path}"])

    # Ajouter les fichiers individuels
    for file in INCLUDE_FILES:
        if os.path.exists(file):
            cmd.extend(["--add-data", f"{file}{os.pathsep}."])

    # Ajouter les infos de version
    cmd.extend(["--version-file", version_file])

    # Spécifier le dossier de sortie
    cmd.extend(["--distpath", args.output_dir])

    # Ajouter le script principal
    cmd.append(MAIN_SCRIPT)

    # Exécuter la commande
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Messages d'erreur/avertissement: {result.stderr}")

        print(
            f"\nBuild terminée avec succès! Le fichier exécutable est disponible dans le dossier '{args.output_dir}'."
        )

        # Nettoyer les fichiers temporaires
        if os.path.exists(version_file):
            os.remove(
                version_file
            )  # Réorganiser les fichiers si mode onedir (pas nécessaire en mode onefile)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la création de l'exécutable: {e}")
        print(f"Sortie standard: {e.stdout}")
        print(f"Erreur standard: {e.stderr}")
        return False


def create_installer(args):
    """Crée un installateur avec Inno Setup (si disponible)"""
    try:
        # Vérifier si Inno Setup est installé
        inno_cmd = r"C:\Program Files (x86)\Inno Setup 6\iscc.exe"

        # Si vous ne connaissez pas le chemin, essayez de le trouver automatiquement
        if not os.path.exists(inno_cmd):
            # Chemins communs où Inno Setup pourrait être installé
            possible_paths = [
                r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
                r"C:\Program Files\Inno Setup 6\iscc.exe",
                r"C:\Program Files (x86)\Inno Setup 5\iscc.exe",
                r"C:\Program Files\Inno Setup 5\iscc.exe",
            ]

            # Vérifier si l'un des chemins existe
            for path in possible_paths:
                if os.path.exists(path):
                    inno_cmd = path
                    break
            else:
                # Essayer de trouver iscc.exe dans le PATH
                for directory in os.environ["PATH"].split(os.pathsep):
                    path = os.path.join(directory, "iscc.exe")
                    if os.path.exists(path):
                        inno_cmd = path
                        break

        # Vérifier que le fichier existe
        if not os.path.exists(inno_cmd):
            print(
                "Inno Setup n'est pas installé ou n'est pas dans le PATH. L'installateur ne sera pas créé."
            )
            print(
                "Pour créer un installateur, installez Inno Setup depuis https://jrsoftware.org/isdl.php"
            )
            return False

        print(f"Utilisation d'Inno Setup à {inno_cmd}")

        print("Création du script d'installation Inno Setup...")

        # Chemin de l'exécutable généré
        if args.onefile:
            exe_path = f"{args.output_dir}/{args.name}.exe"
            source_files = (
                f'Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion'
            )
        else:
            exe_path = f"{args.output_dir}/{args.name}"
            source_files = f'Source: "{exe_path}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs'

        # Vérifier si le fichier de licence existe
        has_license = os.path.exists("LICENSE")
        license_line = (
            'LicenseFile="LICENSE"' if has_license else "; Pas de fichier de licence"
        )

        # Créer le script Inno Setup
        iss_script = f"""
; Script généré par le script de build de {args.name}
; Inno Setup Script

#define MyAppName "{args.name}"
#define MyAppVersion "{args.version}"
#define MyAppPublisher "Warzonefury"
#define MyAppExeName "{args.name}.exe"

[Setup]
; NOTE: La valeur AppId est unique pour cette application.
; Ne pas utiliser la même valeur AppId dans d'autres installateurs.
AppId={{{{98761ABC-01FE-4D61-9E22-C17331AA6123}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
{license_line}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
; Si vous souhaitez que l'installateur requiert des privilèges administrateur
; décommenter la ligne suivante:
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={args.output_dir}
OutputBaseFilename={args.name}-setup-{args.version}
SetupIconFile={args.icon}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
{source_files}

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Dirs]
Name: "{{userappdata}}\{{#MyAppName}}\data"; Permissions: users-full

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
"""

        # Écrire le script Inno Setup dans un fichier
        iss_file = f"{args.name}_installer.iss"
        with open(iss_file, "w", encoding="utf-8") as f:
            f.write(iss_script)

        # Exécuter Inno Setup
        print("Compilation de l'installateur avec Inno Setup...")
        result = subprocess.run(
            [inno_cmd, iss_file], check=True, capture_output=True, text=True
        )

        # Afficher la sortie si nécessaire
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Messages d'avertissement/erreur: {result.stderr}")

        # Nettoyer les fichiers temporaires
        os.remove(iss_file)

        print(
            f"Installation terminée avec succès! L'installateur est disponible dans le dossier '{args.output_dir}'."
        )
        return True

    except (FileNotFoundError, subprocess.CalledProcessError, OSError) as e:
        print(f"Erreur lors de la création de l'installateur: {e}")
        traceback.print_exc()
        return False


# Modifiez la fonction main pour utiliser generate_inno_script au lieu de create_installer
def main():
    """Fonction principale"""
    # Récupérer les arguments
    args = parse_arguments()

    # Nettoyer les dossiers si demandé
    if args.clean:
        clean_build_directories()

    # Créer l'exécutable
    if build_executable(args):
        print(f"Exécutable créé avec succès dans le dossier '{args.output_dir}'.")

        # Demander si l'utilisateur souhaite créer un script d'installation
        print("\nVoulez-vous générer un script d'installation Inno Setup? (o/n)")
        choice = input().lower()
        if choice in ["o", "oui", "y", "yes"]:
            create_installer(args)
    else:
        print("Échec de la création de l'exécutable.")
        sys.exit(1)


if __name__ == "__main__":
    print(f"=== Script de build pour {APP_NAME} v{APP_VERSION} ===")
    main()
