{ package, lib,stdenv, buildFHSEnv, writeShellScript, ...}:
let
  ldPath = lib.optionals stdenv.is64bit [ "/lib64" ] ++ [ "/lib32" ];
  exportLDPath = ''
    export LD_LIBRARY_PATH=${lib.concatStringsSep ":" ldPath}''${LD_LIBRARY_PATH:+:}$LD_LIBRARY_PATH
  '';
in
buildFHSEnv {
  name = "umu";
  runScript = writeShellScript "umu-env" ''
    ${exportLDPath}
    ${package}/bin/umu-run "$@"
  '';
}
