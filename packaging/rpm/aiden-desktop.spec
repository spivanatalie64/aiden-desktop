%global _name aiden-desktop

Name:          %{_name}
Version:       1.0.0
Release:       1%{?dist}
Summary:       AI desktop assistant with code execution, encrypted storage, and LAN mesh

License:       GPL-3.0-or-later
URL:           https://gitlab.acreetionos.org/natalie/aiden-desktop
Source0:       %{url}/-/archive/v%{version}/aiden-desktop-v%{version}.tar.gz

BuildRequires: cargo, npm, nodejs, python3-devel, gtk3-devel, webkit2gtk4.1-devel
BuildRequires: libappindicator-gtk3-devel, librsvg2-devel, libsoup3-devel, openssl-devel
Requires:      python3, gtk3, webkit2gtk4.1, libappindicator-gtk3, librsvg

%description
AIDEN is a powerful AI assistant that runs on your local machine. It provides
conversational AI via OpenRouter, sandboxed code execution, encrypted storage,
LAN mesh caching, and multiple frontends (GTK, Tauri webview, and TUI).

%prep
%autosetup -n aiden-desktop-v%{version}

%build
cd desktop/web
npm ci
npm run build
cd ../..
cargo tauri build --bundles rpm --project-dir desktop/src-tauri

%install
install -Dm755 desktop/src-tauri/target/release/aiden-desktop %{buildroot}%{_bindir}/aiden-desktop
install -Dm644 packaging/org.acreetionos.Aiden.desktop %{buildroot}%{_datadir}/applications/org.acreetionos.Aiden.desktop
install -Dm644 desktop/src-tauri/icons/32x32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/aiden-desktop.png
install -Dm644 desktop/src-tauri/icons/128x128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/aiden-desktop.png
install -Dm644 desktop/src-tauri/icons/128x128@2x.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/aiden-desktop.png

%files
%{_bindir}/aiden-desktop
%{_datadir}/applications/org.acreetionos.Aiden.desktop
%{_datadir}/icons/hicolor/32x32/apps/aiden-desktop.png
%{_datadir}/icons/hicolor/128x128/apps/aiden-desktop.png
%{_datadir}/icons/hicolor/256x256/apps/aiden-desktop.png

%changelog
* Sat May 03 2026 natalie <natalie@acreetionos.org> - 1.0.0-1
- Initial package
