from setuptools import find_packages, setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='json_content_validator',
    version='0.1',
    description='JSON content validator',
    long_description=readme(),
    url='https://github.com/daka83/json_content_validator',
    author='daka83',
    author_email='daka983@gmail.com',
    license='MIT',
    packages=['json_content_validator'],
    python_requires=">=3.5",
    # include_package_data=True,
    zip_safe=False,
)