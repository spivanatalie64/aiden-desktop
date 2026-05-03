{ pkgs ? import <nixpkgs> { } }:

pkgs.stdenv.mkDerivation {
  pname = "aiden-desktop";
  version = "1.0.0";

  src = pkgs.fetchgit {
    url = "https://gitlab.acreetionos.org/natalie/aiden-desktop.git";
    rev = "v1.0.0";
    sha256 = "sha256-0000000000000000000000000000000000000000000000000000=";
  };

  nativeBuildInputs = with pkgs; [ cargo npm nodejs python3 pkg-config ];
  buildInputs = with pkgs; [
    gtk3 webkitgtk_4_1 libappindicator-gtk3 librsvg
    openssl libsoup
  ];

  buildPhase = ''
    cd desktop/web
    npm ci
    npm run build
    cd ../..
    cargo tauri build --bundles deb --project-dir desktop/src-tauri
  '';

  installPhase = ''
    install -Dm755 desktop/src-tauri/target/release/aiden-desktop $out/bin/aiden-desktop
    install -Dm644 packaging/org.acreetionos.Aiden.desktop $out/share/applications/org.acreetionos.Aiden.desktop
    install -Dm644 desktop/src-tauri/icons/32x32.png $out/share/icons/hicolor/32x32/apps/aiden-desktop.png
    install -Dm644 desktop/src-tauri/icons/128x128.png $out/share/icons/hicolor/128x128/apps/aiden-desktop.png
    install -Dm644 desktop/src-tauri/icons/128x128@2x.png $out/share/icons/hicolor/256x256/apps/aiden-desktop.png
    install -Dm644 packaging/org.acreetionos.Aiden.metainfo.xml $out/share/metainfo/org.acreetionos.Aiden.metainfo.xml
  '';

  meta = with pkgs.lib; {
    description = "AI desktop assistant with code execution, encrypted storage, and LAN mesh";
    homepage = "https://gitlab.acreetionos.org/natalie/aiden-desktop";
    license = licenses.gpl3Plus;
    platforms = platforms.linux;
    maintainers = [ "natalie <natalie@acreetionos.org>" ];
  };
}
