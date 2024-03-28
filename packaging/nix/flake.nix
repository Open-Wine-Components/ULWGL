{
  description = "umu universal game launcher";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  outputs = { self, nixpkgs }:
  let
    umu-package = nixpkgs.legacyPackages.x86_64-linux.callPackage ./umu-launcher.nix { umu-launcher=( builtins.toPath "${self}/../../"); };
    umu-run = nixpkgs.legacyPackages.x86_64-linux.callPackage ./umu-run.nix { package=umu-package; };
  in{
    packages.x86_64-linux.umu = nixpkgs.legacyPackages.x86_64-linux.callPackage ./combine.nix { env=umu-run; package=umu-package; };
  };
}
