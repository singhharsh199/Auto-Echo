from setuptools import setup, Extension, find_packages

probe_module = Extension(
    'autoecho.probe_c',
    sources=['src/autoecho/probe/probe.c'],
    extra_compile_args=['-O3']
)

setup(
    name='autoecho',
    version='0.1.0',
    description='Automated Discovery of Memory Hierarchy Latency Patterns',
    author='Harsh Raj Singh',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    ext_modules=[probe_module],
    install_requires=[
        'numpy',
        'pandas',
        'scikit-learn',
        'matplotlib',
        'seaborn'
    ],
)
