project('umu',
    ['cpp'],
    license :  'GPL-3.0-only',
    license_files : ['LICENSE'],
)

subproject('reaper',
    default_options : [
        'prefix=' + get_option('prefix'),
        'bindir=' + get_option('prefix') / get_option('datadir') / meson.project_name(),
    ],
)

subdir('umu')
subdir('docs')
