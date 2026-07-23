from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext


class BuildExt(build_ext):
    """Pick the right optimisation flag per compiler so the C extensions build
    on GCC/Clang (Linux/macOS, -O3) and MSVC (Windows, /O2) alike."""

    def build_extensions(self):
        flag = "/O2" if self.compiler.compiler_type == "msvc" else "-O3"
        for ext in self.extensions:
            ext.extra_compile_args = [flag]
        super().build_extensions()


probe_module = Extension(
    "autoecho.probe_c",
    sources=["src/autoecho/probe/probe.c"],
)

wss_probe_module = Extension(
    "autoecho.wss_probe_c",
    sources=["src/autoecho/wss/wss_probe.c"],
)

setup(
    name="autoecho",
    version="0.2.0",
    description="Automated Discovery of Memory Hierarchy Latency Patterns",
    author="Harsh Raj Singh",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    ext_modules=[probe_module, wss_probe_module],
    cmdclass={"build_ext": BuildExt},
    # 3.11 floor: the pinned scientific stack (numpy 2.4, pandas 3.0, scipy 1.17,
    # scikit-learn 1.9, matplotlib 3.11) all require Python >= 3.11.
    python_requires=">=3.11",
    # Abstract runtime deps; requirements.txt holds the pinned lockfile (same
    # packages, exact versions) used for reproducible results.
    install_requires=[
        "numpy",
        "pandas",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "scipy",
        "ruptures",
    ],
    extras_require={
        # Development / CI tooling: `pip install -e .[dev]`
        "dev": ["pytest", "ruff", "black"],
    },
)
