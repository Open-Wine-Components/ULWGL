fs = import('fs')

configure_file(
    input : 'umu-run.in',
    output : 'umu-run',
    configuration : umu_run_data,
    install : false,
    install_dir : get_option('datadir') / meson.project_name() / fs.name(meson.current_source_dir()),
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'compatibilitytool.vdf',
        'toolmanifest.vdf'
    ],
    install_dir: get_option('datadir') / meson.project_name() / fs.name(meson.current_source_dir()),
)
