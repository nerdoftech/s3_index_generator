import sys
import os
import importlib
from pathlib2 import PurePosixPath

sys.path.append('%s/lib' % os.path.dirname(__file__))
import s3lib
import consts
import log_utils

get_log_levels = log_utils.getLoggingLevels

def parse_dir_name(raw_path):
    path = PurePosixPath(raw_path)
    if path.parts[0] == consts.aps:
        path = PurePosixPath(consts.aps.join( path.parts[1:]))
    return path

def s3_index_run(options):
    log = log_utils.getLogger(options.log_level, options.log_config)
    s3lib.setLogger(log)
    log.trace('s3_index_run args %s: ' % options)
    # Import user specified html template or the default
    if options.html_template:
        try:
            template_file = importlib.import_module(options.html_template)
            create_html_index = getattr(template_file, 'create_html_index')
        except Exception as err:
            log.fatal('Import of HTML template failed: ' + err.message)
            exit(1)
    else:
        from default_html_index import create_html_index

    target_dir = parse_dir_name(options.target_dir)
    if options.root_dir:
        root_dir = parse_dir_name(options.root_dir)
        s3_objs = s3lib.recursive_index_search(
            options.bucket,
            target_dir,
            root_dir,
            options.obj_name,
            options.ignore_pattern
        )
    else:
        s3_objs = s3lib.single_index_search(
            options.bucket,
            target_dir,
            options.obj_name,
            options.ignore_pattern
        )
    log.trace('directory search s3 objects: %s' % s3_objs)
    uploaded_indexs = []
    for dir_name, dir_objs in s3_objs:
        s3_obj_path = str(dir_name) + consts.index_file
        log.debug('Creating index file for ' + s3_obj_path)
        log.trace('create_html_index dir objects: %s' % dir_objs)
        html = create_html_index(str(dir_name), str(dir_name.parent), dir_objs)
        log.trace('%s %s %s' % ('--------------',  s3_obj_path, '-------------- '))
        log.trace(html)

        if not options.no_upload:
            log.debug('Preparing to upload index file.')
            uploaded_indexs.append([
                    s3lib.upload_file_to_s3(options.bucket, html.encode(), s3_obj_path),
                    s3_obj_path
            ])
        else:
            # File creation will go here
            pass

    # Fix this when there are no sucessful uploads
    if len(uploaded_indexs):
        log.info('The following index pages have been uploaded:')
        unloaded_indexs = []
        for status, index_file in uploaded_indexs:
            if status:
                log.info('- ' + index_file)
    else:
        log.info('No index pages have been uploaded.')