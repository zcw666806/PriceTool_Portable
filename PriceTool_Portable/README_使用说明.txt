UK Order 价格查询工具

运行方式
1. 开发电脑：安装 requirements-dev.txt 后，双击 启动工具.bat。
2. 便携版：将嵌入式 Python 放入 PriceTool_Portable/python 后，双击 启动工具.bat。
3. 页面地址：http://127.0.0.1:8501

主要流程
1. 在“导入工作台”填写 PDF 文件夹。
2. Excel 文件为可选项，每行一个路径。
3. 点击“开始识别”。
4. 在“汇总查询”按产品、尺寸、Tier、Cover Range 等条件筛选。
5. 在“异常复核”查看价格为空、尺寸无法识别、版本冲突等数据。
6. 在“导出结果”生成整理后的 Excel。

默认路径
PDF 文件夹：C:/other/UK_Order/FOB 2026 JULY PRICE LIST

输出位置
导出的 Excel 会保存到 output/ 文件夹。
