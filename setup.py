from setuptools import setup, find_packages

setup(
    name='s3_index_generator',
    version='0.1',
    description='Package to create and upload index.html files to AWS S3 bucket directories.',
    url='https://github.com/nerdoftech/s3_index_generator',
    author='Eric Flores',
    author_email='ericflorescode@gmail.com',
    license='MIT',
    packages=find_packages(),
    scripts=['bin/s3-index-generator'],
    python_requires='>=2.5,<3.*',
    install_requires=[
      'boto3',
      'pathlib2',
    ],
    zip_safe=False,
    include_package_data=True
)
