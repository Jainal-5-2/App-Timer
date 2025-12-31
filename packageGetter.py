from main import getForegroundApp
import subprocess
import sys

def getLauncher():
    command = 'sudo pm resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME'.split(' ')
    pm = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    intent = pm.stdout.split('\n')[1]
    return intent

def getPackageByPattern(pattern):
    command = 'sudo cmd package list packages'.split(' ')
    packages = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    packages = packages.stdout.split('\n')

    results = []

    for i in packages:
        if pattern in i:
            results.append(i)

    return results

if len(sys.argv) > 1:
    result = getPackageByPattern(sys.argv[1])

    print(f'Results: {len(result)}')
    for i in result:
        print(i.split(':')[1])
    
    sys.exit(1)

launcher = getLauncher()
while True:
    package = getForegroundApp()

    if package:
        if package == 'com.termux' or package in launcher:
            continue

        subprocess.run(
            ['termux-clipboard-set',
            package]
        )

        break