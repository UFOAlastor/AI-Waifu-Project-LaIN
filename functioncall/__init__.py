# __init__.py
import importlib.util
from pathlib import Path
import sys


def _get_package_dir():
    """安全获取当前包目录"""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        raise RuntimeError("必须在文件系统中运行（不支持打包环境）")


def load_custom_functions():
    """
    自动加载同目录下的所有函数文件
    返回格式: (函数描述列表, 函数实现字典)
    """
    package_dir = _get_package_dir()
    func_files = package_dir.glob("*.py")

    all_funcs = []
    implementations = {}

    for file in func_files:
        if file.name.startswith("__"):  # 跳过自身
            continue

        # 动态创建唯一模块名
        module_name = f"user_funcs.{file.stem}"
        if module_name in sys.modules:
            continue  # 避免重复加载

        try:
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            if hasattr(module, "functions"):
                all_funcs.extend(module.functions)

                for func_def in module.functions:
                    func_name = func_def["name"]
                    if hasattr(module, func_name):
                        implementations[func_name] = getattr(module, func_name)
        except Exception as e:
            print(f"加载 {file.name} 失败: {str(e)}")

    return all_funcs, implementations


# 可选：自动加载（根据需求决定是否启用）
# __all_functions, __function_impls = load_custom_functions()
