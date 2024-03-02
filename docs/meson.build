scdoc = find_program('scdoc')

custom_target('man1',
    input : 'umu.1.scd',
    output : 'umu.1',
    command : [ scdoc ],
    feed : true,
    capture : true,
    install : true,
    install_dir : get_option('mandir'),
)

custom_target('man5',
    input : 'umu.5.scd',
    output : 'umu.5',
    command : [ scdoc ],
    feed : true,
    capture : true,
    install : true,
    install_dir : get_option('mandir'),
)