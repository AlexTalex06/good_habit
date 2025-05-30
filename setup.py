from setuptools import setup, find_packages

setup(
    name='good_habit',
    version='0.1',
    packages=find_packages(include=['good_habit', 'good_habit.*']),
    include_package_data=True,
    install_requires=[
        'pyramid',
        'pyramid_jinja2',
        'SQLAlchemy',
        'pymysql',
        'waitress',
    ],
    entry_points={
        'paste.app_factory': [
            'main = good_habit:main',
        ],
    },
)