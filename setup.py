from setuptools import setup, find_packages

setup(
    name="cloudflare-ddns-updater",  # Name of the package
    version="1.0.1",
    packages=find_packages(),  # Automatically find and include your Python files
    include_package_data=True,  # Include files specified in MANIFEST.in
    package_data={
            'cloudflare_ddns_updater': ['constants.py'],  # Adjust the path as needed
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
    author="Roberto Giusti",  # Your details
    author_email="rgiusti@gmail.com",
    description="A Python tool to update Cloudflare DNS automatically using DDNS.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cloudflare-ddns-updater",  # Your project URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",

    ],
    python_requires=">=3.10",  # Minimum Python version
)
