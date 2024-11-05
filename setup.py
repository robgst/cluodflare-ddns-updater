from setuptools import setup, find_packages

setup(
    name="cloudflare-ddns-updater",
    version="1.0.2",
    packages=find_packages(),
    include_package_data=True,
    package_data={
            'cloudflare_ddns_updater': ['constants.py'],
        },
    install_requires=[
        "requests",
        "python-crontab",
        "setuptools"
    ],
    entry_points={
        "console_scripts": [
            "cloudflare-ddns-updater  = cloudflare_ddns_updater.initializer:main",
            'ip-updater = cloudflare_ddns_updater.ip_updater:main',
        ]
    },
    author="Roberto Giusti",
    author_email="rgiusti@gmail.com",
    description="A Python tool to update Cloudflare DNS automatically using DDNS.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/robgst/cloudflare-ddns-updater",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",

    ],
    python_requires=">=3.10",
)
