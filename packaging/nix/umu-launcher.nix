{stdenv , umu-launcher, pkgs, ...}:
stdenv.mkDerivation {
  pname = "umu-launcher";
  version = "0.1";
  src = umu-launcher;
  depsBuildBuild = [
    pkgs.meson
    pkgs.ninja
    pkgs.scdoc
  ];
  dontUseMesonConfigure = true;
  dontUseNinjaBuild = true;
  dontUseNinjaInstall = true;
  dontUseNinjaCheck = true;
  configureScript = "./configure.sh";
}
