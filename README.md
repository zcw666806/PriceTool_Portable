# UK Order Local Price Tool

本项目根据 `项目设计方案.md` 构建：本地 Streamlit 页面读取 PDF 价格表，可选导入业务 Excel，统一整理为长表，支持筛选、异常复核和 Excel 导出。

## 开发运行

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
streamlit run app\streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

也可以双击 `start_tool.cmd`。如果在便携包内运行，脚本会使用包内 `python/`；如果在开发目录运行，脚本会使用 `runtime/python/`。

## 核心目录

- `app/streamlit_app.py`：本地页面
- `src/`：PDF、Excel、SQLite、清洗、导出核心逻辑
- `config/`：默认路径和映射规则
- `data/`：SQLite 数据库
- `output/`：导出的 Excel
- `tests/`：核心规则测试

## 便携构建

运行 `package_release.cmd` 直接生成便携 zip。脚本会从 `runtime/python/` 复制已安装依赖的嵌入式 Python，不再需要长期维护 `PriceTool_Portable/` 目录。
