# Contributing to FulfillCrew

感谢您对 FulfillCrew（智仓通）项目的关注！我们欢迎并感谢您任何形式的贡献。

## 如何贡献

### 报告 Bug

如果您发现了 Bug，请通过 [GitHub Issues](../../issues) 提交，并尽量包含以下信息：

- 问题的清晰描述
- 复现步骤
- 期望行为与实际行为
- 环境信息（操作系统、Python/Node.js 版本等）
- 相关日志或截图

### 提交功能请求

如果您有新功能的想法，请：

1. 先搜索现有 Issues，避免重复
2. 创建新 Issue，描述您的想法和使用场景
3. 等待维护者反馈后再开始编码

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -am 'feat: add some feature'`
4. 推送到分支：`git push origin feature/my-feature`
5. 提交 Pull Request

#### 提交信息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/Jeffhan789/FulfillCrew.git
cd FulfillCrew

# 后端（Python）
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 前端（Node.js）
cd frontend
npm install

# 数据清洗（Node.js）
node data_cleaning/data_processing.js \
  data_cleaning/raw_products/products.json \
  data_cleaning/cleaned_products/products.json

# 运行测试
pytest tests/ -v
cd frontend && npm test
```

### 代码规范

- Python 代码遵循 PEP 8
- JavaScript/TypeScript 代码使用项目现有风格
- 新增功能请配套相应的测试
- 确保所有测试通过后再提交 PR

## 行为准则

请保持友好和尊重，共同为社区创造积极的协作环境。

## 许可

通过提交代码，您同意您的贡献将在项目相同的 [LICENSE](../LICENSE) 下发布。
