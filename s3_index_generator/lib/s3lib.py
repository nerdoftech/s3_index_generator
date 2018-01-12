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
        response = _list_objects(bucket, consts.aps.join(target_dir.parts), continue_token)
        if 'Contents' in response:
            contents.extend(response['Contents'])
        if not response['IsTruncated']:
            break
        continue_token = response['NextContinuationToken']

    return contents

def _search_objects(target_dir, s3_objects, obj_name='', ignore_pattern=''):
    log.trace('_search_objects args: %s' % locals())
    target_dir_num_folders = len(target_dir.parts)
    matched_objects = set()
    for obj in s3_objects:
        obj_next_path_list = obj['Key'].split(consts.aps)[0 : target_dir_num_folders + 1]
        obj_next_path_string = consts.aps.join(obj_next_path_list)
        obj_path_instance = PurePosixPath(obj['Key'])

        if ignore_pattern:
            if re.search(ignore_pattern, obj_path_instance.name):
                continue

        if obj_name:
            # Look for matches to obj_name
            if (obj_next_path_list[target_dir_num_folders] == obj_name):
                matched_objects.add(obj_next_path_string)
        else:
            matched_objects.add(obj_next_path_string)

    return sorted([obj for obj in matched_objects], reverse=True)

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
        log.fatal('Error with root dir and target dir: "%s"\n' % e.mesage)
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
