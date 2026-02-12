import subprocess
import sys
import os

blender_python = sys.executable
blender_site_packages = os.path.join(os.path.dirname(blender_python), "..", "lib", "site-packages")

def install_packages():
    packages = ['PySide6']
    for package in packages:
        try:
            subprocess.check_call([
                blender_python,
                '-m', 'pip', 'install',
                '--target', blender_site_packages,
                '--upgrade', package
            ])
            print(f"Installation de {package} dans Blender : OK")
        except Exception as e:
            print(f"Erreur installation {package} : {e}")

if __name__ == "__main__":
    print("Installation des paquets dans le dossier de Blender...")
    install_packages()
    print("Script terminé.")
