with import <nixpkgs> { };

let
  pp = python311Packages;
in pkgs.mkShell rec {
  name = "impurePythonEnv";
  venvDir = "./.venv";
  buildInputs = [
    pkgs.stdenv.cc.cc.lib
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    pkgs.gcc
    pkgs.glibc
    pkgs.zlib
    pkgs.openssl
    pkgs.libffi
    pkgs.gnumake
    pkgs.pkg-config
    pkgs.python311Packages.cffi
    pkgs.python311Packages.numpy
  ];

  # Create the virtual environment
  shellHook = ''
    if [ ! -d "$venvDir" ]; then
      python -m venv "$venvDir"
      source "$venvDir/bin/activate"
      pip install --upgrade pip setuptools wheel
      # Temporarily switch to a compatible version of Python
      pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client fpdf2 qrcode Pillow ephem pytz pylunar
    else
      source "$venvDir/bin/activate"
    fi
    exec zsh
  '';
}
