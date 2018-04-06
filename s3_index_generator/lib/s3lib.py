import sys
import re
import boto3
import consts
from pathlib2 import PurePosixPath

client = boto3.client('s3')
s3 = boto3.resource('s3')
log = None

def setLogger(logger):
    global log
    log = logger

def _list_objects(bucket, prefix, continue_token):
    log.trace('_list_objects args: %s' % locals())
    list_objects_args = {
                'Bucket': bucket,
                'EncodingType': 'url',
    }
    if prefix: list_objects_args['Prefix'] = prefix
    if continue_token: list_objects_args['ContinuationToken'] = continue_token
    try:
        return client.list_objects_v2(**list_objects_args)
    except Exception as e:
        log.fatal('Error in _list_objects: "%s"\n' % e.message)
        exit(1)

def _get_list_of_s3_objects(bucket, target_dir):
    log.trace('_get_list_of_s3_objects args: %s' % locals())
    contents = []
    continue_token = ''
    while True:
        response = _list_objects(bucket, str(target_dir), continue_token)
        if 'Contents' in response:
            log.trace('_get_list_of_s3_objects _list_objects result len: %d' % len(response['Contents']))
            contents.extend(response['Contents'])
        if not response['IsTruncated']:
            break
        continue_token = response['NextContinuationToken']
    log.trace('_get_list_of_s3_objects result len: %d' % len(contents))
    return contents

def _search_objects(target_dir, s3_objects, s3_obj_name='', ignore_pattern=''):
    log.trace('_search_objects args: %s' % str({
        'target_dir': target_dir,
        's3_objects len': len(s3_objects),
        's3_obj_name': s3_obj_name,
        'ignore_pattern': ignore_pattern
    }))
    matched_objects = set()
    for s3_obj in s3_objects:
        s3_obj_path = PurePosixPath(s3_obj['Key'])
        try:
            obj_rel_path = s3_obj_path.relative_to(target_dir)
        except ValueError as e:
            log.trace('_search_objects s3_obj not relative_to target_dir: %s' % e.message)
            continue
        obj_next_path_list = target_dir.joinpath(obj_rel_path.parts[0])
        obj_next_path_string = str(obj_next_path_list)
        log.trace('_search_objects s3_obj_path: ' + str(s3_obj_path))
        log.trace('_search_objects obj_next_path_string: ' + obj_next_path_string)

        if ignore_pattern:
            if re.search(ignore_pattern, s3_obj_path.name):
                continue

        if s3_obj_name:
            # Look for matches to obj_name
            if re.search(s3_obj_name, s3_obj_path.name):
                matched_objects.add(s3_obj)
        else:
            matched_objects.add(obj_next_path_string)
    results = sorted([obj for obj in matched_objects], reverse=True)
    log.trace('_search_objects results: %s' % results)
    return results

def single_index_search(bucket, target_dir, obj_name='', ignore_pattern=''):
    log.trace('single_index_search args: %s' % locals())
    s3_objects = _get_list_of_s3_objects(bucket, target_dir)
    return [[target_dir, _search_objects(target_dir, s3_objects, obj_name, ignore_pattern)]]

def recursive_index_search(bucket, target_dir, root_dir, obj_name='', ignore_pattern=''):
    log.trace('recursive_index_search args: %s' % locals())
    s3_objects = _get_list_of_s3_objects(bucket, root_dir)
    # Root dir not part of target dir will make pathlib throw
    try:
        rel_path = target_dir.relative_to(root_dir).parts
    except ValueError as e:
        log.fatal('Error with root dir and target dir: "%s"\n' % e.message)
        exit(1)
    objs_in_each_dir = []
    objs_in_each_dir.append(
        [root_dir, _search_objects(root_dir, s3_objects, obj_name, ignore_pattern)]
    )
    for index, _ in enumerate(rel_path):
        target_dir_to_search = PurePosixPath(consts.aps.join(root_dir.parts + rel_path[:index + 1]))
        objs = _search_objects(target_dir_to_search, s3_objects, obj_name, ignore_pattern)
        objs_in_each_dir.append([target_dir_to_search, objs])

    return objs_in_each_dir

def upload_file_to_s3(bucket, body, s3_obj_path):
    log.trace('upload_file_to_s3 args: %s' % locals())
    s3_bucket_instance = s3.Bucket(bucket)
    log.debug('Uploading index file for ' + s3_obj_path)
    try:
        s3_bucket_instance.put_object(
            Body = body,
            ContentType = consts.index_file_content_type,
            Key = s3_obj_path,
        )
    except Exception as e:
        log.error('Error uploading "%s": %s' % (s3_obj_path, e.message))
        return False
    return True
