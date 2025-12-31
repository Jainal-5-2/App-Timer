from main import getForegroundApp
import subprocess

while True:
    package = getForegroundApp()

    if package:
        subprocess.run(
            'termux-clipboard-set',
            package
        )

        break