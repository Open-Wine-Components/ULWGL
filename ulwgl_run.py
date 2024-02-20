#!/usr/bin/env python3

import os
import argparse
from traceback import print_exception
from argparse import ArgumentParser, Namespace
import sys
from pathlib import Path
import tomllib
from typing import Dict, Any, List, Set, Union, Tuple
import ulwgl_plugins
from re import match
import subprocess
from ulwgl_dl_util import get_ulwgl_proton


def parse_args() -> Union[Namespace, Tuple[str, List[str]]]:  # noqa: D103
    opt_args: Set[str] = {"--help", "-h", "--config", "-v", "--version"}
    exe: str = Path(__file__).name
    usage: str = f"""
example usage:
  WINEPREFIX= GAMEID= PROTONPATH= {exe} /home/foo/example.exe
  WINEPREFIX= GAMEID= PROTONPATH= {exe} /home/foo/example.exe -opengl
  WINEPREFIX= GAMEID= PROTONPATH= {exe} ""
  WINEPREFIX= GAMEID= PROTONPATH= PROTON_VERB= {exe} /home/foo/example.exe
  WINEPREFIX= GAMEID= PROTONPATH= STORE= {exe} /home/foo/example.exe
  {exe} --config /home/foo/example.toml
    """
    parser: ArgumentParser = argparse.ArgumentParser(
        description="Unified Linux Wine Game Launcher",
        epilog=usage,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config", help="path to TOML file")
    parser.add_argument("-v", "--version", action="store_true", help="print version")

    if not sys.argv[1:]:
        err: str = "Please see project README.md for more info and examples.\nhttps://github.com/Open-Wine-Components/ULWGL-launcher"
        parser.print_help(sys.stderr)
        raise SystemExit(err)

    if sys.argv[1:][0] in opt_args:
        return parser.parse_args(sys.argv[1:])

    return sys.argv[1], sys.argv[2:]


def get_versions(paths: List[Path]) -> str:
    """Return the version of this launcher and all of its associated tools declared in the config file.

    NOTE: The following table is required: [ulwgl.versions]
    """
    version: str = ""

    for path in paths:
        if path.is_file():
            toml: Dict[str, Any] = None

            with path.open(mode="rb") as file:
                toml = tomllib.load(file)

            if (
                "ulwgl" in toml
                and "versions" in toml["ulwgl"]
                and "launcher" in toml["ulwgl"]["versions"]
            ):
                exe: str = Path(__file__).name
                launcher: str = toml["ulwgl"]["versions"]["launcher"]
                tools: str = "\n".join(
                    [
                        f"{key}: {val}"
                        for key, val in toml["ulwgl"]["versions"].items()
                        if key != "launcher"
                    ]
                )
                version = f"{exe} {launcher}\n\n{tools}"

                break

    return version


def setup_pfx(path: str) -> None:
    """Create a symlink to the WINE prefix and tracked_files file."""
    pfx: Path = Path(path).joinpath("pfx").expanduser()

    if pfx.is_symlink():
        pfx.unlink()

    if not pfx.is_dir():
        pfx.symlink_to(Path(path).expanduser())

    Path(path).joinpath("tracked_files").expanduser().touch()


def check_env(
    env: Dict[str, str], toml: Dict[str, Any] = None
) -> Union[Dict[str, str], Dict[str, Any]]:
    """Before executing a game, check for environment variables and set them.

    WINEPREFIX, GAMEID and PROTONPATH are strictly required.
    """
    if toml:
        # Check for required or empty key/value pairs when reading a TOML config
        # NOTE: Casing matters in the config and we don't check if the game id is set
        table: str = "ulwgl"
        required_keys: List[str] = ["proton", "prefix", "exe"]

        if table not in toml:
            err: str = f"Table '{table}' in TOML is not defined."
            raise ValueError(err)

        for key in required_keys:
            if key not in toml[table]:
                err: str = f"The following key in table '{table}' is required: {key}"
                raise ValueError(err)

            # Raise an error for executables that do not exist
            # One case this can happen is when game options are appended at the end of the exe
            # Users should use launch_args for that
            if key == "exe" and not Path(toml[table][key]).expanduser().is_file():
                val: str = toml[table][key]
                err: str = f"Value for key '{key}' in TOML is not a file: {val}"
                raise FileNotFoundError(err)

            # The proton and wine prefix need to be folders
            if (
                key == "proton" and not Path(toml[table][key]).expanduser().is_dir()
            ) or (key == "prefix" and not Path(toml[table][key]).expanduser().is_dir()):
                dir: str = Path(toml[table][key]).expanduser().as_posix()
                err: str = f"Value for key '{key}' in TOML is not a directory: {dir}"
                raise NotADirectoryError(err)

        # Check for empty keys
        for key, val in toml[table].items():
            if not val and isinstance(val, str):
                err: str = f"Value is empty for '{key}' in TOML.\nPlease specify a value or remove the following entry:\n{key} = {val}"
                raise ValueError(err)

        return toml

    if "WINEPREFIX" not in os.environ:
        err: str = "Environment variable not set or not a directory: WINEPREFIX"
        raise ValueError(err)

    if not Path(os.environ["WINEPREFIX"]).expanduser().is_dir():
        Path(os.environ["WINEPREFIX"]).mkdir(parents=True)
    env["WINEPREFIX"] = os.environ["WINEPREFIX"]

    if "GAMEID" not in os.environ:
        err: str = "Environment variable not set: GAMEID"
        raise ValueError(err)
    env["GAMEID"] = os.environ["GAMEID"]

    if "PROTONPATH" not in os.environ:
        os.environ["PROTONPATH"] = ""
        get_ulwgl_proton(env)
    elif Path("~/.local/share/Steam/compatibilitytools.d/" + os.environ["PROTONPATH"]).expanduser().is_dir():
        env["PROTONPATH"] = Path("~/.local/share/Steam/compatibilitytools.d/").expanduser().joinpath(os.environ["PROTONPATH"])
    elif not Path(os.environ["PROTONPATH"]).expanduser().is_dir():
        os.environ["PROTONPATH"] = ""
        get_ulwgl_proton(env)
    else:
        env["PROTONPATH"] = os.environ["PROTONPATH"]

    print(env["PROTONPATH"])

    # If download fails/doesn't exist in the system, raise an error
    if not os.environ["PROTONPATH"]:
        err: str = "Download failed.\nProton could not be found in cache or compatibilitytools.d\nPlease set $PROTONPATH or visit https://github.com/Open-Wine-Components/ULWGL-Proton/releases"
        raise FileNotFoundError(err)

    return env


def set_env(
    env: Dict[str, str], args: Union[Namespace, Tuple[str, List[str]]]
) -> Dict[str, str]:
    """Set various environment variables for the Steam RT.

    Filesystem paths will be formatted and expanded as POSIX
    """
    verbs: Set[str] = {
        "waitforexitandrun",
        "run",
        "runinprefix",
        "destroyprefix",
        "getcompatpath",
        "getnativepath",
    }

    # PROTON_VERB
    # For invalid Proton verbs, just assign the waitforexitandrun
    if "PROTON_VERB" in os.environ and os.environ["PROTON_VERB"] in verbs:
        env["PROTON_VERB"] = os.environ["PROTON_VERB"]
    else:
        env["PROTON_VERB"] = "waitforexitandrun"

    # EXE
    # Empty string for EXE will be used to create a prefix
    if isinstance(args, tuple) and isinstance(args[0], str) and not args[0]:
        env["EXE"] = ""
        env["STEAM_COMPAT_INSTALL_PATH"] = ""
        env["PROTON_VERB"] = "waitforexitandrun"
    elif isinstance(args, tuple):
        env["EXE"] = Path(args[0]).expanduser().as_posix()
        env["STEAM_COMPAT_INSTALL_PATH"] = Path(env["EXE"]).parent.as_posix()
    else:
        # Config branch
        env["EXE"] = Path(env["EXE"]).expanduser().as_posix()
        env["STEAM_COMPAT_INSTALL_PATH"] = Path(env["EXE"]).parent.as_posix()

    if "STORE" in os.environ:
        env["STORE"] = os.environ["STORE"]

    # ULWGL_ID
    env["ULWGL_ID"] = env["GAMEID"]
    env["STEAM_COMPAT_APP_ID"] = "0"

    if match(r"^ulwgl-[\d\w]+$", env["ULWGL_ID"]):
        env["STEAM_COMPAT_APP_ID"] = env["ULWGL_ID"][env["ULWGL_ID"].find("-") + 1 :]
    env["SteamAppId"] = env["STEAM_COMPAT_APP_ID"]
    env["SteamGameId"] = env["SteamAppId"]

    # PATHS
    env["WINEPREFIX"] = Path(env["WINEPREFIX"]).expanduser().as_posix()
    env["PROTONPATH"] = Path(env["PROTONPATH"]).expanduser().as_posix()
    env["STEAM_COMPAT_DATA_PATH"] = env["WINEPREFIX"]
    env["STEAM_COMPAT_SHADER_PATH"] = env["STEAM_COMPAT_DATA_PATH"] + "/shadercache"
    env["STEAM_COMPAT_TOOL_PATHS"] = (
        env["PROTONPATH"] + ":" + Path(__file__).parent.as_posix()
    )
    env["STEAM_COMPAT_MOUNTS"] = env["STEAM_COMPAT_TOOL_PATHS"]

    return env


def set_env_toml(env: Dict[str, str], args: Namespace) -> Dict[str, str]:
    """Read a TOML file then sets the environment variables for the Steam RT.

    In the TOML file, certain keys map to Steam RT environment variables. For example:
          proton -> $PROTONPATH
          prefix -> $WINEPREFIX
          game_id -> $GAMEID
          exe -> $EXE
    At the moment we expect the tables: 'ulwgl'
    """
    toml: Dict[str, Any] = None
    path_config: str = Path(getattr(args, "config", None)).expanduser().as_posix()

    if not Path(path_config).is_file():
        msg: str = "Path to configuration is not a file: " + getattr(
            args, "config", None
        )
        raise FileNotFoundError(msg)

    with Path(path_config).open(mode="rb") as file:
        toml = tomllib.load(file)

    check_env(env, toml)

    for key, val in toml["ulwgl"].items():
        if key == "prefix":
            env["WINEPREFIX"] = val
        elif key == "game_id":
            env["GAMEID"] = val
        elif key == "proton":
            env["PROTONPATH"] = val
        elif key == "store":
            env["STORE"] = val
        elif key == "exe":
            if toml.get("ulwgl").get("launch_args"):
                env["EXE"] = val + " " + " ".join(toml.get("ulwgl").get("launch_args"))
            else:
                env["EXE"] = val
    return env


def build_command(
    env: Dict[str, str], command: List[str], opts: List[str] = None
) -> List[str]:
    """Build the command to be executed."""
    paths: List[Path] = [
        Path.home().joinpath(".local/share/ULWGL/ULWGL"),
        Path(__file__).parent.joinpath("ULWGL"),
    ]
    entry_point: str = ""
    verb: str = env["PROTON_VERB"]

    # Find the ULWGL script in $HOME/.local/share then cwd
    for path in paths:
        if path.is_file():
            entry_point = path.as_posix()
            break

    # Raise an error if the _v2-entry-point cannot be found
    if not entry_point:
        home: str = Path.home().as_posix()
        dir: str = Path(__file__).parent.as_posix()
        msg: str = (
            f"Path to _v2-entry-point cannot be found in: {home}/.local/share or {dir}"
        )
        raise FileNotFoundError(msg)

    if not Path(env.get("PROTONPATH")).joinpath("proton").is_file():
        err: str = "The following file was not found in PROTONPATH: proton"
        raise FileNotFoundError(err)

    command.extend([entry_point, "--verb", verb, "--"])
    command.extend(
        [
            Path(env.get("PROTONPATH")).joinpath("proton").as_posix(),
            verb,
            env.get("EXE"),
        ]
    )

    if opts:
        command.extend([*opts])

    return command


def main() -> int:  # noqa: D103
    env: Dict[str, str] = {
        "WINEPREFIX": "",
        "GAMEID": "",
        "PROTON_CRASH_REPORT_DIR": "/tmp/ULWGL_crashreports",
        "PROTONPATH": "",
        "STEAM_COMPAT_APP_ID": "",
        "STEAM_COMPAT_TOOL_PATHS": "",
        "STEAM_COMPAT_LIBRARY_PATHS": "",
        "STEAM_COMPAT_MOUNTS": "",
        "STEAM_COMPAT_INSTALL_PATH": "",
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": "",
        "STEAM_COMPAT_DATA_PATH": "",
        "STEAM_COMPAT_SHADER_PATH": "",
        "FONTCONFIG_PATH": "",
        "EXE": "",
        "SteamAppId": "",
        "SteamGameId": "",
        "STEAM_RUNTIME_LIBRARY_PATH": "",
        "STORE": "",
        "PROTON_VERB": "",
        "ULWGL_ID": "",
    }
    command: List[str] = []
    args: Union[Namespace, Tuple[str, List[str]]] = parse_args()
    opts: List[str] = None

    if isinstance(args, Namespace) and getattr(args, "version", None):
        paths: List[Path] = [
            Path(__file__).parent.joinpath("ULWGL_VERSIONS.toml"),
            Path("/usr/share/ULWGL/ULWGL_VERSIONS.toml"),
        ]

        print(get_versions(paths), file=sys.stderr)

        return 0

    if isinstance(args, Namespace):
        set_env_toml(env, args)
    else:
        # Reference the game options
        opts = args[1]
        check_env(env)

    setup_pfx(env["WINEPREFIX"])
    set_env(env, args)

    # Game Drive
    ulwgl_plugins.enable_steam_game_drive(env)

    # Set all environment variables
    # NOTE: `env` after this block should be read only
    for key, val in env.items():
        os.environ[key] = val

    build_command(env, command, opts)
    return subprocess.run(command).returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print_exception(e)
        sys.exit(1)
