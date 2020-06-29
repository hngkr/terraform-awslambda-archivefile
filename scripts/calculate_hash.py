#!/usr/bin/env python3
#
# Build Lambda function with no binary dependencies
#
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

# -- main --

@terraform_external_data
def main(query):
    file_path = query['file_path']
    filename = os.path.basename(file_path)

    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            file_data = f.read()
            sha256 = hashlib.sha256(file_data).hexdigest()
            md5 = hashlib.md5(file_data).hexdigest()
    else:
        sha256 = ""
        md5 = ""

    return {'filename': filename, 'path': file_path, 'sha256': sha256, 'md5': md5}


if __name__ == "__main__":
    main()
