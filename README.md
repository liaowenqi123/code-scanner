# Code Scanner Plus - 代码审查辅助工具

一个用于扫描代码库中常见问题并生成报告的命令行工具。参考 [fuck-u-code](https://github.com/Done-0/fuck-u-code) 的设计思路，覆盖复杂度、规模、注释、错误处理、命名、重复、结构等七大检查维度，并对代码质量进行 0-100 分量化评分。

## 功能特性

### 安全与习惯检查

- **SecretScanner**: 检测硬编码的敏感信息（AWS Key、GitHub Token等）
- **TodoScanner**: 检测TODO/FIXME注释及其年龄
- **ImportScanner**: 检测未使用的import语句

### 复杂度（Complexity）

- **ComplexityScanner**: 计算每个函数的圈复杂度（McCabe），超过阈值（默认10）告警；同时检测最大嵌套深度（默认超过5层告警）

### 规模（Size）

- **FunctionLengthScanner**: 检测超过80行的函数
- **LineLengthScanner**: 检测超过120字符的长行
- **ArgumentScanner**: 检测参数超过6个的函数

### 错误处理（Error Handling）

- **ErrorHandlingScanner**: 检测裸 `except:`、`except Exception:` 捕获后直接 `pass`（吞掉异常）等问题

### 命名（Naming）

- **NamingScanner**: 检测命名规范违规——函数/变量应为 `snake_case`，类应为 `PascalCase`，模块级常量应为 `UPPER_SNAKE_CASE`

### 重复（Duplication）

- **DuplicateCodeScanner**: 通过 AST 指纹检测结构重复的函数体

### 结构（Structure）

- **MagicNumberScanner**: 检测函数体中的魔法数字（默认排除 0、1、-1、2、100 等常见值）
- **MutableDefaultScanner**: 检测可变默认参数（`def f(x=[])`）
- **GlobalScanner**: 检测 `global` 语句的使用

### 注释（Comments）

- **CommentsScanner**: 检测注释比例过低（<10%）或过高（>60%）的文件，以及缺少 docstring 的公开函数/类/模块

### 质量评分

扫描完成后输出 0-100 的质量总分，每个问题按严重程度扣分：

| 严重级别 | 扣分 | 说明 |
| -------- | ---- | ---- |
| high     | 5分  | 高风险问题（敏感信息、裸except等） |
| medium   | 3分  | 中风险问题（超长函数、魔法数字等） |
| low      | 1分  | 低风险问题（命名、注释等） |

同时输出 high / medium / low 问题的等级分布。

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
5. **圈复杂度** - 超过10的函数
6. **嵌套深度** - 超过5层的嵌套
7. **超长行** - 超过120字符的行
8. **错误处理** - 裸except、吞掉异常
9. **命名规范** - 不符合PEP8的命名
10. **魔法数字** - 未命名的裸数字
11. **重复代码** - 结构重复的函数体
12. **可变默认参数** - 危险的默认参数
13. **参数过多** - 超过6个参数
14. **global滥用** - 使用global语句
15. **注释质量** - 注释比例异常、缺少docstring

## 示例输出

```
运行 secret 扫描器...
运行 function_length 扫描器...
运行 import 扫描器...
运行 todo 扫描器...
运行 complexity 扫描器...
运行 line_length 扫描器...
运行 error_handling 扫描器...
运行 naming 扫描器...
运行 magic_number 扫描器...
运行 duplicate 扫描器...
运行 structure 扫描器...
运行 comments 扫描器...

扫描完成！
扫描文件数: 13
secret: 2 个问题
function_length: 1 个问题
import: 10 个问题
todo: 2 个问题
complexity: 3 个问题
line_length: 5 个问题
error_handling: 1 个问题
naming: 4 个问题
magic_number: 6 个问题
duplicate: 1 个问题
structure: 2 个问题
comments: 2 个问题

质量评分: 62/100
等级分布: high=3, medium=12, low=6
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
│       ├── todo.py
│       ├── complexity.py
│       ├── line_length.py
│       ├── error_handling.py
│       ├── naming.py
│       ├── magic_number.py
│       ├── duplicate.py
│       ├── structure.py
│       └── comments.py
├── tests/                  # 测试文件
└── pyproject.toml         # 项目配置
```

## License

MIT
