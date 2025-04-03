from pathlib import Path
import shutil

while True:
    app_name = input("App Name: ")
    if not app_name:
        break
    if Path(f"osFiles/Software/{app_name}").exists():
        shutil.rmtree(f"osFiles/Software/{app_name}")
    Path(f"deviceFiles/Software/{app_name}.json").unlink(missing_ok=True)
