git = find_program('git')

umu_run_data = configuration_data()
umu_run_data.set('INSTALL_PATH', get_option('prefix') / get_option('datadir') / meson.project_name())
configure_file(
    input : 'umu-run.in',
    output : 'umu-run',
    configuration : umu_run_data,
    install : true,
    install_dir : get_option('bindir'),
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'umu_consts.py',
        'umu_dl_util.py',
        'umu_log.py',
        'umu_plugins.py',
        'umu_util.py',
    ],
    install_dir: get_option('datadir') / meson.project_name(),
)
install_data(
    [
        'umu_run.py',
    ],
    install_dir: get_option('datadir') / meson.project_name(),
    install_mode: 'rwxr-xr-x',
)

umu_desc = run_command(
    git, '-C', meson.source_root(), 'describe', '--always', '--long', '--tags', check: true
).stdout().strip()
reaper_desc = run_command(
    git, '-C', meson.source_root() / 'subprojects/reaper', 'describe', '--always', '--long', '--tags', check: true
).stdout().strip()
umu_version_data = configuration_data()
umu_version_data.set('UMU_VERSION', umu_desc)
umu_version_data.set('REAPER_VERSION', umu_desc)
configure_file(
    input : 'umu_version.json.in',
    output : 'umu_version.json',
    configuration : umu_version_data,
    install : true,
    install_dir: get_option('datadir') / meson.project_name(),
)

subdir('umu-launcher')
