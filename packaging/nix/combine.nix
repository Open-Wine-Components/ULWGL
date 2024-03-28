{ env, package, symlinkJoin }:
symlinkJoin {
  name = "umu-combine";
  paths = [
    env
    package
  ];
  postBuild = ''
    rm $out/bin/umu-run
  '';
}
