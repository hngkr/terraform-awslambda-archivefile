#!/usr/bin/env python3
#
# Build Lambda function with no binary dependencies
#
import contextlib
import distutils.dir_util
import distutils.file_util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile


# -- helpers

@contextlib.contextmanager
def environ(**env):
    """Set the environment variables

    Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards
    """
    original_env = {key: os.getenv(key) for key in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for key, value in original_env.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


@contextlib.contextmanager
def cd(path):
    """Set the working directory

    Temporarily set the working directory inside the context manager and
    reset it to the previous working directory afterwards
    """
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


# -- main functions

def main(args):
    with tempfile.TemporaryDirectory(prefix="/tmp/") as workdir:

        tf_requirements_file = os.environ.get('REQUIREMENTS_FILE', None)
        tf_project_path = os.environ.get('PROJECT_PATH')
        tf_lib_path = os.environ.get('LIB_PATH', 'null')
        tf_output_filepath = os.environ.get('OUTPUT_FILEPATH')
        tf_runtime = os.environ.get('RUNTIME')

        install_script = 'install.bash'
        requirements_file = 'requirements.txt'
        install_bash_script_filepath = os.path.join(workdir, install_script)
        requirements_filepath = os.path.join(workdir, requirements_file)
        project_dirpath = workdir

        distutils.dir_util.copy_tree(tf_project_path, project_dirpath)

        if tf_requirements_file:
            distutils.file_util.copy_file(tf_requirements_file, requirements_filepath)

        if tf_lib_path and tf_lib_path != 'null':
            lib_dirpath = os.path.join(workdir, 'lib')
            pathlib.Path(lib_dirpath).mkdir(parents=True, exist_ok=True)
            distutils.dir_util.copy_tree(tf_lib_path, lib_dirpath)

        with open(install_bash_script_filepath, "w") as bash_script:
            # pip seems more stable now, so disabling automatic upgrade (could be an option?)
            # bash_script.write("python -m pip install --upgrade pip\n")
            bash_script.write(f"mkdir -p .dist\n")
            bash_script.write(f"cp -R * .dist\n")
            bash_script.write(f"rm -f .dist/{install_script} .dist/{requirements_file}\n")
            bash_script.write(f"pip install --target ./.dist -r {requirements_file} --no-deps --disable-pip-version-check\n")
            if tf_lib_path and tf_lib_path != 'null':
                bash_script.write(f"mkdir -p .dist/lib/{tf_runtime}/site-packages\n")
                bash_script.write(f"cp -r lib/* .dist/lib/{tf_runtime}/site-packages/\n")
            bash_script.write(f"find .dist -type f -name '*.pyc' -delete\n")
            bash_script.write("exit 0\n")

        docker_command = f"docker run --rm -v {workdir}:/work -w /work lambci/lambda:build-{tf_runtime} bash -e {install_script}"
        subprocess.check_call(docker_command.split(' '))

        archive_name = os.path.splitext(tf_output_filepath)[0]
        shutil.make_archive(archive_name, "zip", root_dir=os.path.join(workdir, ".dist"))



if __name__ == "__main__":
    main(sys.argv)
