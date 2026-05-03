# Template file for 'aiden-desktop'
pkgname = "aiden-desktop"
version = "1.0.0"
revision = "1"
archs = ["x86_64"]
build_style = "simple"
make_build_target = "desktop/src-tauri/target/release/aiden-desktop"
hostmakedepends = ["cargo", "npm", "nodejs", "python3"]
makedepends = ["gtk3-devel", "webkit2gtk4.1-devel", "librsvg-devel", "libsoup3-devel"]
depends = ["python3", "gtk3", "webkit2gtk4.1", "librsvg"]
short_desc = "AI desktop assistant with code execution, encrypted storage, and LAN mesh"
maintainer = "natalie <natalie@acreetionos.org>"
license = "GPL-3.0-or-later"
homepage = "https://gitlab.acreetionos.org/natalie/aiden-desktop"
distfiles = [f"https://gitlab.acreetionos.org/natalie/aiden-desktop/-/archive/v{version}/aiden-desktop-v{version}.tar.gz"]
checksum = ["SKIP"]

def do_build(self):
    self.cd("desktop/web")
    self.do("npm", "ci")
    self.do("npm", "run", "build")
    self.cd("../..")
    self.do("cargo", "tauri", "build", "--bundles", "deb", "--project-dir", "desktop/src-tauri")

def do_install(self):
    self.install_bin("desktop/src-tauri/target/release/aiden-desktop")
    self.install_file("packaging/org.acreetionos.Aiden.desktop", "usr/share/applications")
    self.install_file("desktop/src-tauri/icons/32x32.png", "usr/share/icons/hicolor/32x32/apps/aiden-desktop.png")
    self.install_file("desktop/src-tauri/icons/128x128.png", "usr/share/icons/hicolor/128x128/apps/aiden-desktop.png")
    self.install_file("desktop/src-tauri/icons/128x128@2x.png", "usr/share/icons/hicolor/256x256/apps/aiden-desktop.png")
