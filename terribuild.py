import json
import os
from urllib.parse import urlparse
import sys

cwd = os.getcwd()

def installPackage(packagename, packageinfo):
    if not os.path.isdir(os.path.join("packages", packagename)):
        if "url" in packageinfo:
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
        elif "git" in packageinfo:
            url = packageinfo["git"]
            os.system(f"git clone --depth=1 {url}")
            pass
        else:
            exit(f"Neither url or git found in package {packagename}")

        # 
        # Build package
        if packageinfo['compile_commands']:
            print(packageinfo["compile_commands"])
            os.system(packageinfo['compile_commands'])

with open('terribuild.json') as f:
    configurationText = f.read()
    configuration = json.loads(configurationText)

if not 'build_tools' in configuration:
    exit("No build tools specified in configuration")

installPackage('build_tools', configuration['build_tools'])

# First, get all dependencies
for packagename, packageinfo in configuration['packages'].items():
    installPackage(packagename, packageinfo)

build_tools = configuration['build_tools']
compiler = os.path.join(cwd, "packages", "build_tools", build_tools['root'], build_tools['compiler'])
linker = os.path.join(cwd, "packages", "build_tools", build_tools['root'], build_tools['linker'])
cflags = configuration['cflags']
ldflags = configuration['ldflags']

built = []

def build(binaryName:str, cflags: str, ldflags: str):
    if not binaryName in configuration["binaries"]:
        exit(f"Unable to find {binaryName} in configuration")

    binaryConfig = configuration["binaries"][binaryName]

    if not "type" in binaryConfig:
        exit(f"Cannot find type for ${binaryName}")

    outputName = binaryName
    if "name" in binaryConfig:
        outputName = binaryConfig["name"]

    isLibrary = binaryConfig["type"] == "library"

    print(f"Building {binaryConfig['type']} {binaryName}")
    thisBinaryCFlags = ""
    if "cflags" in binaryConfig:
        thisBinaryCFlags = thisBinaryCFlags + " " + " ".join(binaryConfig["cflags"])
    thisBinaryLDFlags = ""
    if "ldflags" in binaryConfig:
        thisBinaryLDFlags = thisBinaryLDFlags + " " + " ".join(binaryConfig["ldflags"])

    if "include" in binaryConfig:
        for include in binaryConfig["include"]:
            thisBinaryCFlags = thisBinaryCFlags + f" -I{os.path.join(cwd, include)}"

    if not "sources" in binaryConfig:
        exit(f"No sources defined in binary {binaryName}")

    if not "dest" in binaryConfig:
        exit(f"No destination defined in binary {binaryName}")

    objects = []
    for source in binaryConfig["sources"]:
        objectFileDir = os.path.join(cwd, binaryConfig['dest'], os.path.dirname(source))
        print(f"Creating {objectFileDir}\n")
        os.makedirs(objectFileDir, exist_ok=True)
        objectFilePath = os.path.join(cwd, binaryConfig['dest'], f"{source}.o")
        command = f"{compiler} {cflags} {thisBinaryCFlags} -fpic -c {os.path.join(cwd, source)} -o {objectFilePath}"
        print(f"Creating {os.path.join(cwd, configuration['binaries'][binaryName]['dest'])}\n")
        os.makedirs(os.path.join(cwd, configuration['binaries'][binaryName]['dest']), exist_ok=True)
        print(command)
        os.system(command)
        objects.append(objectFilePath)

    command = linker
    if isLibrary:
        command = command + " -shared"
        binaryExt = ".so"
        binaryPrefix = "lib"
    else:
        binaryExt = ""
        binaryPrefix = ""
    command = command + f" -o {os.path.join(cwd, binaryConfig['dest'], binaryPrefix + outputName + binaryExt)} {ldflags} {thisBinaryLDFlags} {' '.join(objects)}"
    print(command)
    os.system(command)
    built.append(binaryName)

    if isLibrary:
        thisBinaryLDFlags = thisBinaryLDFlags + f"-L{os.path.join(cwd, binaryConfig['dest'])} -l{outputName}"

    return thisBinaryCFlags, thisBinaryLDFlags

def build_deps(binary: str, cflags: str, ldflags: str):
    if not binary in configuration['binaries']:
        if not binary in configuration['packages']:
            exit(f"Unable to find dependency {binary}")

    if 'dependencies' in configuration['binaries'][binary]:
        for dependency in configuration['binaries'][binary]['dependencies']:
            if not dependency in built:
                cflags, ldflags = build_deps(dependency, cflags, ldflags)

    return build(binary, cflags, ldflags)

if len(sys.argv) == 0:
    exit("You must specify a binary to build")

build_deps(sys.argv[1], cflags, ldflags)

# for libraryname, librarydata in configuration['libraries'].items():
#     sources = librarydata['sources']
#     extracflags = " ".join(librarydata['cflags'])
#     extraldflags = " ".join(librarydata['ldflags'])

#     print(f"Building {libraryname}")
#     print(f"  Dependencies:")
#     print(f"    {librarydata['dependencies']}")
#     print(f"  Sources:")
#     print(f"    {sources}")
#     os.makedirs(librarydata['dest'], exist_ok=True)
#     objects = []
#     for source in sources:
#         objectFileDir = f"{librarydata['dest']}/{os.path.dirname(source)}"
#         os.makedirs(objectFileDir, exist_ok=True)
#         objectFilePath = f"{librarydata['dest']}/{source}.o"
#         command = f"{compiler} {cflags} {extracflags} -fpic -c {source} -o {objectFilePath}"
#         os.makedirs(librarydata['dest'], exist_ok=True)
#         print(command)
#         os.system(command)
#         objects.append(objectFilePath)
    
#     command = f"{linker} -shared -o {librarydata['dest']}/{libraryname}.so {ldflags} {extraldflags} {' '.join(objects)}"
#     print(command)
#     os.system(command)

# for binaryName, binaryData in configuration['binaries'].items():
#     sources = binaryData['sources']
#     extracflags = " ".join(binaryData['cflags'])
#     extraldflags = " ".join(binaryData['ldflags'])
#     dependencies = binaryData['dependencies']

#     for dependency in dependencies:
#         if dependency in configuration['packages']:
#             for ldpath in configuration['packages'][dependency]['ldpaths']:
#                 extraldflags = extraldflags + " -Lpackages/" + dependency + "/" + configuration['packages'][dependency]['root'] + "/" + ldpath
#             for lib in configuration['packages'][dependency]['libs']:
#                 extraldflags = extraldflags + " -l" + lib
#             for path in configuration['packages'][dependency]['include']:
#                 extracflags = extracflags + " -Ipackages/" + dependency + "/" + configuration['packages'][dependency]['root'] + "/" + path

#         if dependency in configuration['libraries']:
#             extraldflags = extraldflags + " -L" + configuration['libraries'][dependency]['dest']
#             for lib in configuration['libraries'][dependency]['libs']:
#                 extraldflags = extraldflags + " -l" + lib
#             for path in configuration['libraries'][dependency]['include']:
#                 extracflags = extracflags + " -I" + path

#     print(f"Building {binaryName}")
#     print(f"  Dependencies:")
#     print(f"    {dependencies}")
#     print(f"  Sources:")
#     print(f"    {sources}")
#     objects = []
#     os.makedirs(binaryData['dest'], exist_ok=True)
#     for source in sources:
#         objectFileDir = f"{binaryData['dest']}/{os.path.dirname(source)}"
#         os.makedirs(objectFileDir, exist_ok=True)
#         command = f"{compiler} {cflags} {extracflags} -c {source} -o {binaryData['dest']}/{source}.o"
#         print(command)
#         os.system(command)
#         objects.append(f"{binaryData['dest']}/{source}.o")

#     command = f"{linker} -o {binaryData['dest']}/{binaryName} {' '.join(objects)} {ldflags} {extraldflags}"
#     print(command)
#     os.system(command)
