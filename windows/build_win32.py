# --------------------------------------------------------------------
# For the complete Windows build procedure, please read
# README-BUILD-win32.txt .
#
# Some general advice for building PyGTK-based Windows .EXEs can be
# found here:
# http://www.no-ack.org/2010/09/complete-guide-to-py2exe-for-pygtk.html
# --------------------------------------------------------------------

import os
from os import path
import sys
import shutil
import glob
import subprocess
import distutils.dir_util
from distutils.sysconfig import get_python_lib

os.chdir(path.dirname(path.dirname(path.realpath(__file__))))

# --------------------------------------
# CONFIG AND PATHS
# --------------------------------------

BUILD_ROOT = r"windows\build"
EXE_ROOT = path.join(BUILD_ROOT, "ZimDesktopWiki")

# GTK Runtime

GTK_ROOT = path.join(get_python_lib(), "gtk-2.0", "runtime")
if not path.exists(GTK_ROOT):
	raise RuntimeError("Can't find GTK.")

# Find VC90 Redistributable

VC90_DLL = glob.glob(r"C:\Windows\winsxs\x86_microsoft.vc90.crt*9.0.21022.8*")
VC90_MANIFEST = glob.glob(r"C:\Windows\winsxs\Manifests\x86_microsoft.vc90.crt*9.0.21022.8*.manifest")
if VC90_DLL == None or VC90_MANIFEST == None:
	raise RuntimeError("Can't find VC 9.0 runtime DLL.")
VC90_DLL = VC90_DLL[0]
VC90_MANIFEST = VC90_MANIFEST[0]

# NSIS compiler

MAKENSIS = path.join(os.environ["PROGRAMFILES"], r"NSIS\makensis.exe")
if not path.exists(MAKENSIS):
	if "PROGRAMFILES(X86)" in os.environ:
		MAKENSIS = path.join(os.environ["PROGRAMFILES(x86)"], r"NSIS\makensis.exe")
	if not path.exists(MAKENSIS):
		raise RuntimeError("Can't find makensis.exe .")

# --------------------------------------
# BUILD
# --------------------------------------

# Clean up and initialize the build directory
# (Use cmd.exe because shutil.rmtree seems to fail to delete "Microsoft.VC90.CRT" folder.)

if path.exists(BUILD_ROOT):
	subprocess.check_call([
		"cmd.exe", "/c",
		"cd", "/d", os.getcwd(), "&&",
		"rmdir" , "/s", "/q", BUILD_ROOT
	])
os.makedirs(EXE_ROOT)

# Create main zim.exe and any files generated by setup.py

subprocess.check_call(['python.exe', 'setup.py', 'build'])
subprocess.check_call(['python.exe', 'setup.py', 'py2exe', '--dist-dir', EXE_ROOT])

# Copy GTK runtime

print("Copying GTK runtime...")

distutils.dir_util.copy_tree(path.join(GTK_ROOT, "etc"), path.join(EXE_ROOT, "etc"), update=1)
distutils.dir_util.copy_tree(path.join(GTK_ROOT, "lib"), path.join(EXE_ROOT, "lib"), update=1)

for f in os.listdir(path.join(GTK_ROOT, "share")):
	if not f in ["doc", "gtk-doc", "icons", "man"]:
		distutils.dir_util.copy_tree(path.join(GTK_ROOT, "share", f), path.join(EXE_ROOT, "share", f), update=1)

distutils.dir_util.copy_tree(
	path.join(GTK_ROOT, "share", "icons", "hicolor"),
	path.join(EXE_ROOT, "share", "icons", "hicolor"),
	update=1
)

shutil.copy(path.join(GTK_ROOT, "bin", "libxml2-2.dll"), EXE_ROOT)
shutil.copy(path.join(GTK_ROOT, "bin", "librsvg-2-2.dll"), EXE_ROOT)
shutil.copy(path.join(GTK_ROOT, "bin", "gspawn-win32-helper.exe"), EXE_ROOT)
shutil.copy(path.join(GTK_ROOT, "bin", "gspawn-win32-helper-console.exe"), EXE_ROOT)

print("Done copying GTK runtime.")

# Copy Zim's data, icons, and translation folders

shutil.copytree("data", path.join(EXE_ROOT, "data"))
distutils.dir_util.copy_tree("icons", path.join(EXE_ROOT, "icons"), update=1)
distutils.dir_util.copy_tree("locale", path.join(EXE_ROOT, "locale"), update=1)

# Copy jpeg62.dll

shutil.copy(r"windows\lib\jpeg62.dll", EXE_ROOT)

# Copy VC90 Redistributable

vc90_target = path.join(EXE_ROOT, "Microsoft.VC90.CRT")
shutil.copytree(VC90_DLL, vc90_target)
shutil.copy(VC90_MANIFEST, path.join(vc90_target, "Microsoft.VC90.CRT.manifest"))

# Set theme to MS-Windows

f = open(path.join(EXE_ROOT, r"etc\gtk-2.0\gtkrc"), "w")
print >>f, 'gtk-theme-name = "MS-Windows"'
f.close()

# Compile Launchers

print("Building launchers...")

for nsi in [
	"zim_debug.nsi",
	"Zim Desktop Wiki Portable (Debug Mode).nsi",
	"Zim Desktop Wiki Portable.nsi"
]:
	subprocess.check_call([MAKENSIS, path.join(r"windows\src\launchers", nsi)])

print("Done building launchers.")
