#!/usr/bin/env python3
#
# Build Lambda function with no binary dependencies
#
import base64
import contextlib
import datetime
import glob
import hashlib
import json
import os
import sys
from functools import wraps


# -- helpers --

# vendored in from: https://github.com/operatingops/terraform_external_data

def error(message):
    """
    Errors must create non-zero status codes and human-readable, ideally one-line, messages on stderr.
    """
    print(message, file=sys.stderr)
    sys.exit(1)


def validate(data):
    """
    Query data and result data must have keys who's values are strings.
    """
    if not isinstance(data, dict):
        error('Data must be a dictionary.')
    for value in data.values():
        decode_operation = getattr(value, "decode", None)
        if callable(decode_operation):
            decoded_value = value.decode()
            if not isinstance(value, str) or isinstance(decoded_value, str):
                error('Values must be strings.')
        else:
            if not isinstance(value, str):
                error('Values must be strings.')


def terraform_external_data(function):
    """
    Query data is received on stdin as a JSON object.
    Result data must be returned on stdout as a JSON object.
    The wrapped function must expect its first positional argument to be a dictionary of the query data.
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        query = json.loads(sys.stdin.read())
        validate(query)
        try:
            result = function(query, *args, **kwargs)
        except Exception as e:
            # Terraform wants one-line errors so we catch all exceptions and trim down to just the message (no trace).
            error('{}: {}'.format(type(e).__name__, e))
        validate(result)
        sys.stdout.write(json.dumps(result))
    return wrapper

# -- assorted helpers --

@contextlib.contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)

def hash_file(file_path, digest=None):
    if digest is None:
        digest = hashlib.sha1()

    if os.path.isfile(file_path):
        with open(file_path, 'rb') as f_obj:
            while True:
                buf = f_obj.read(1024 * 1024)
                if not buf:
                    break
                digest.update(buf)
    else:
        raise FileNotFoundError

    return digest.hexdigest()

def hash_directory(path):
    digest = hashlib.sha1()

    if not os.path.exists(path):
        raise FileNotFoundError

    for root, dirs, files in sorted(os.walk(path)):
        for names in files:

            # ignore .git, .gitkeep and requirements.txt
            if root.find("/.git") != -1:
                continue
            if names in [".gitkeep", "requirements.txt"]:
                continue

            file_path = os.path.join(root, names)
            digest.update(hashlib.sha1(file_path[len(path):].encode()).digest())
            hash_file(file_path, digest)

    return digest.hexdigest()

def find_old_identifier(output_glob_filepath):
    glob_found = glob.glob(output_glob_filepath)
    return glob_found[0] if len(glob_found) == 1 else None

# -- main --

@terraform_external_data
def main(query):
    query['project_path_hash'] = hash_directory(query['project_path'])
    with contextlib.suppress(FileNotFoundError):
        query['lib_path_hash'] = hash_directory(query['lib_path'])

    with contextlib.suppress(FileNotFoundError):
        query['requirements_file_hash'] = hash_file(query['requirements_file'])

    sha1 = hashlib.sha1(json.dumps(query).encode())
    function_name = query["name"]

    # determine if the resulting zipfile already exists with the right content:
    output_path = query["output_path"]
    output_filepattern = "{}_{{}}.zip".format(function_name)
    output_glob_filepath = "{}/{}".format(output_path, output_filepattern.format("*"))

    # Search for a file with an existing identifier
    output_zipfile_path = find_old_identifier(output_glob_filepath)
    if not output_zipfile_path:
        # If file wasn't found, return new identifier based on timestamp
        identifier_base = "{}{}".format(datetime.datetime.utcnow().isoformat(), function_name)
        identifier_sha = hashlib.sha1(identifier_base.encode())
        identifier = base64.urlsafe_b64encode(identifier_sha.digest()).decode()[:16]
        output_zipfile_path = "{}/{}".format(output_path, output_filepattern.format(identifier))

    return {'sha': sha1.hexdigest(),
            'output_filepath': output_zipfile_path,
            'isodate': datetime.datetime.now().isoformat()}


if __name__ == "__main__":
    main()
