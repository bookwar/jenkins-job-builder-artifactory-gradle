from setuptools import setup

setup(
    name='jenkins-job-builder-artifactory-gradle',
    version='0.0.1',
    description='Jenkins Job Builder Artifactory Gradle integration wrapper',
    url='https://github.com/bookwar/jenkins-job-builder-artifactory-gradle',
    author='Aleksandra Fedorova',
    author_email='alpha@bookwar.info',
    license='MIT license',
    install_requires=[],
    entry_points={
        'jenkins_jobs.wrappers': [
            'artifactory-gradle = jenkins_jobs_artifactory_gradle.artifactory_gradle:artifactory_gradle']},
    packages=['jenkins_jobs_artifactory_gradle'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'])
