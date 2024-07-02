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
        if os.path.splitext(filename)[1] == ".xz":
            print("tar xxvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
            os.system("tar xxvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
        if os.path.splitext(filename)[1] == ".bz2":
            print("tar xjvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
            os.system("tar xjvf " + os.path.join("packages", filename) + " -C " + os.path.join("packages", packagename))
        
        if packageinfo['compile_commands']:
            print(packageinfo["compile_commands"])
            os.system(packageinfo['compile_commands'])


build_tools = configuration['packages']['build_tools']
compiler = os.path.join("packages", "build_tools", build_tools['root'], "bin", build_tools['compiler'])
linker = os.path.join("packages", "build_tools", build_tools['root'], "bin", build_tools['linker'])
cflags = configuration['cflags']
ldflags = configuration['ldflags']

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
    os.makedirs(librarydata['dest'], exist_ok=True)
    objects = []
    for source in sources:
        objectFileDir = f"{librarydata['dest']}/{os.path.dirname(source)}"
        os.makedirs(objectFileDir, exist_ok=True)
        objectFilePath = f"{librarydata['dest']}/{source}.o"
        command = f"{compiler} {cflags} {extracflags} -fpic -c {source} -o {objectFilePath}"
        os.makedirs(librarydata['dest'], exist_ok=True)
        print(command)
        os.system(command)
        objects.append(objectFilePath)
    
    command = f"{linker} -shared -o {librarydata['dest']}/{libraryname}.so {ldflags} {extraldflags} {' '.join(objects)}"
    print(command)
    os.system(command)

for programname, programdata in configuration['programs'].items():
    sources = programdata['sources']
    extracflags = " ".join(programdata['cflags'])
    extraldflags = " ".join(programdata['ldflags'])
    dependencies = programdata['dependencies']

    for dependency in dependencies:
        if dependency in configuration['packages']:
            for ldpath in configuration['packages'][dependency]['ldpaths']:
                extraldflags = extraldflags + " -Lpackages/" + dependency + "/" + configuration['packages'][dependency]['root'] + "/" + ldpath
            for lib in configuration['packages'][dependency]['libs']:
                extraldflags = extraldflags + " -l" + lib
            for path in configuration['packages'][dependency]['include']:
                extracflags = extracflags + " -Ipackages/" + dependency + "/" + configuration['packages'][dependency]['root'] + "/" + path

        if dependency in configuration['libraries']:
            extraldflags = extraldflags + " -L" + configuration['libraries'][dependency]['dest']
            for lib in configuration['libraries'][dependency]['libs']:
                extraldflags = extraldflags + " -l" + lib
            for path in configuration['libraries'][dependency]['include']:
                extracflags = extracflags + " -I" + path

    print(f"Building {programname}")
    print(f"  Dependencies:")
    print(f"    {dependencies}")
    print(f"  Sources:")
    print(f"    {sources}")
    objects = []
    os.makedirs(programdata['dest'], exist_ok=True)
    for source in sources:
        objectFileDir = f"{programdata['dest']}/{os.path.dirname(source)}"
        os.makedirs(objectFileDir, exist_ok=True)
        command = f"{compiler} {cflags} {extracflags} -c {source} -o {programdata['dest']}/{source}.o"
        print(command)
        os.system(command)
        objects.append(f"{programdata['dest']}/{source}.o")

    command = f"{linker} -o {programdata['dest']}/{programname} {' '.join(objects)} {ldflags} {extraldflags}"
    print(command)
    os.system(command)
