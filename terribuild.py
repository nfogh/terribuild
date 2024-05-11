import json
import os
from urllib.parse import urlparse
import sys

cwd = os.getcwd()

with open('terribuild.json') as f:
    configurationText = f.read()
    configuration = json.loads(configurationText)

for packagename, packageinfo in configuration['packages'].items():
    if not os.path.isdir(os.path.join("packages", packagename)):
        url = packageinfo["url"]
        filename = os.path.basename(urlparse(url).path)
        if not os.path.exists(os.path.join("packages", filename)):
            print(f"Downloading {packagename} from {url} to packages/{filename}")
            os.system("wget -Ppackages " + url)

        print(f"Extracting {filename}")
        os.mkdir(os.path.join("packages", packagename))
        if os.path.splitext(filename)[1] == ".gz":
            print("tar xzvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
            os.system("tar xzvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
        if os.path.splitext(filename)[1] == ".bz2":
            print("tar xjvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
            os.system("tar xjvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))


build_tools = configuration['packages']['build_tools']
compiler = os.path.join("packages", "build_tools", build_tools['root'], "bin", build_tools['compiler'])
linker = os.path.join("packages", "build_tools", build_tools['root'], "bin", build_tools['linker'])
cflags = configuration['cflags']
dynamiclinker = os.path.join(cwd, "packages", "build_tools", build_tools['root'], "x86_64-buildroot-linux-gnu", "sysroot", "lib", 'ld-linux-x86-64.so.2')
rpath = os.path.join(cwd, "packages", "build_tools", build_tools['root'], "lib64")
rpath2 = os.path.join(cwd, "packages", "build_tools", build_tools['root'], "x86_64-buildroot-linux-gnu", "sysroot", "lib")
rpath3 = os.path.join(cwd, "packages", "build_tools", build_tools['root'], "x86_64-buildroot-linux-gnu", "lib64")
ldflags = configuration['ldflags'] + f"-Wl,-dynamic-linker={dynamiclinker}" f"-Wl,-rpath={rpath} -Wl,-rpath={rpath2} -Wl,-rpath={rpath3} 

if len(sys.argv) == 0:
    toBuild = list(configuration['libraries'].keys()) + list(configuration['programs'].keys())
else:
    toBuild = sys.argv

print("To build")
print(toBuild)

for libraryname, librarydata in configuration['libraries'].items():
    sources = librarydata['sources']
    extracflags = " ".join(librarydata['cflags'])
    extraldflags = " ".join(librarydata['ldflags'])

    print(f"Building {libraryname}")
    print(f"  Dependencies:")
    print(f"    {librarydata['dependencies']}")
    print(f"  Sources:")
    print(f"    {sources}")
    objects = []
    for source in sources:
        command = f"{compiler} {cflags} {extracflags} -fpic -c {source} -o {source}.o"
        print(command)
        os.system(command)
        objects.append(source + ".o")
    command = f"{linker} -shared -o {libraryname}.so {ldflags} {extraldflags} {' '.join(objects)}"
    print(command)
    os.system(command)

for programname, programdata in configuration['programs'].items():
    sources = programdata['sources']
    extracflags = " ".join(programdata['cflags'])
    extraldflags = " ".join(programdata['ldflags'])
    dependencies = programdata['dependencies']

    print(f"Building {programname}")
    print(f"  Dependencies:")
    print(f"    {dependencies}")
    print(f"  Sources:")
    print(f"    {sources}")
    objects = []
    for source in sources:
        command = f"{compiler} {cflags} {extracflags} -c {source} -o {source}.o"
        print(command)
        os.system(command)
        objects.append(source + ".o")

    command = f"{linker} -o {programname} {' '.join(objects)} {ldflags} {extraldflags}"
    print(command)
    os.system(command)
