import glob
import os

from conans import ConanFile, CMake, tools


class LibFlannConan(ConanFile):
    name = "flann"
    description = "Fast Library for Approximate Nearest Neighbors"
    topics = "conan", "flann"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.cs.ubc.ca/research/flann/"
    license = "BSD-3-Clause"
    exports_sources = "CMakeLists.txt"
    generators = "cmake", "cmake_find_package"

    version = "1.9.1"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_hdf5": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_hdf5": False
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    _cmake = None

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    def requirements(self):
        if self.options.with_hdf5:
            self.requires("hdf5/1.10.6")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        # Workaround issue with empty sources for a CMake target
        flann_cpp_dir = os.path.join(self._source_subfolder, "src", "cpp")
        tools.save(os.path.join(flann_cpp_dir, "empty.cpp"), "\n")

        tools.replace_in_file(
            os.path.join(flann_cpp_dir, "CMakeLists.txt"),
            'add_library(flann_cpp SHARED "")',
            'add_library(flann_cpp SHARED empty.cpp)'
        )
        tools.replace_in_file(
            os.path.join(flann_cpp_dir, "CMakeLists.txt"),
            'add_library(flann SHARED "")',
            'add_library(flann SHARED empty.cpp)'
        )

    def _configure_cmake(self):
        if self._cmake is not None:
            return self._cmake
        self._cmake = CMake(self)

        self._cmake.definitions["BUILD_C_BINDINGS"] = True

        # Only build the C++ libraries
        self._cmake.definitions["BUILD_DOC"] = False
        self._cmake.definitions["BUILD_EXAMPLES"] = False
        self._cmake.definitions["BUILD_TESTS"] = False
        self._cmake.definitions["BUILD_MATLAB_BINDINGS"] = False
        self._cmake.definitions["BUILD_PYTHON_BINDINGS"] = False

        # OpenMP support can be added later if needed
        self._cmake.definitions["USE_OPENMP"] = False

        # Workaround issue with flann_cpp
        if self.settings.os == "Windows" and self.options.shared:
            self._cmake.definitions["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True

        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
