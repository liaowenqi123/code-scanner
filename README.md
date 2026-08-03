# Code Scanner - 代码审查辅助工具

一个用于扫描代码库中常见问题并生成报告的命令行工具。

## 功能特性

- **SecretScanner**: 检测硬编码的敏感信息（AWS Key、GitHub Token等）
- **FunctionLengthScanner**: 检测超过80行的函数
- **ImportScanner**: 检测未使用的import语句
- **TodoScanner**: 检测TODO/FIXME注释及其年龄

## 安装

```bash
pip install code-scanner-plus
```

或从源码安装：

```bash
pip install -e .
```

## 使用方法

### 扫描代码

```bash
# 扫描当前目录（默认JSON格式）
python -m code_scanner.cli scan

# 扫描指定目录
python -m code_scanner.cli scan --path /path/to/project

# 输出为Markdown格式（输出到控制台）
python -m code_scanner.cli scan --output markdown

# 输出为Markdown格式（保存到文件）
python -m code_scanner.cli scan --output markdown --file report.md
```

### 生成自检报告

```bash
python -m code_scanner.cli self-report .
```

## 测试

```bash
pytest tests/ -v
```

## 扫描结果说明

工具会扫描所有Python文件并报告：

1. **敏感信息** - 硬编码的密码、API Key等
2. **超长函数** - 超过80行的函数
3. **未使用导入** - 未被使用的import语句
4. **TODO/FIXME** - 待办事项和需要修复的问题

## 示例输出

```
运行 secret 扫描器...
运行 function_length 扫描器...
运行 import 扫描器...
运行 todo 扫描器...

扫描完成！
扫描文件数: 13
secret: 2 个问题
function_length: 1 个问题
import: 10 个问题
todo: 2 个问题
```

## 项目结构

```
code-scanner/
├── src/code_scanner/
│   ├── cli.py              # 命令行接口
│   └── scanners/           # 扫描器模块
│       ├── secret.py
│       ├── function_length.py
│       ├── imports.py
│       └── todo.py
├── tests/                  # 测试文件
└── pyproject.toml         # 项目配置
```

## License

MIT