from __future__ import annotations

import sys
import subprocess
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services import (  # noqa: E402
    export_current,
    get_dashboard_summary,
    get_prices,
    get_table,
    load_config,
    preview_pdf_folder,
    start_import,
)


st.set_page_config(page_title="UK Order 价格查询", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; }
    div[data-testid="stMetric"] {
        background: #f6f8fb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main() -> None:
    config = load_config()
    st.title("UK Order 价格查询")
    st.caption("本工具用于本地识别 PDF 价格表，并可选合并业务 Excel，所有数据都保存在当前工具目录内。")

    default_pdf = config.get("default_pdf_folder", "")

    if "pdf_folder" not in st.session_state:
        st.session_state["pdf_folder"] = default_pdf
    if "pdf_folder_manual" not in st.session_state:
        st.session_state["pdf_folder_manual"] = st.session_state["pdf_folder"]
    if "last_filters" not in st.session_state:
        st.session_state["last_filters"] = {}

    summary = get_dashboard_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("价格行", f"{summary['price_count']:,}")
    c2.metric("待复核", f"{summary['review_count']:,}")
    c3.metric("来源文件", f"{summary['source_count']:,}")
    c4.metric("产品数", f"{summary['product_count']:,}")

    tabs = st.tabs(["导入工作台", "汇总查询", "异常复核", "来源文件", "导出结果"])
    with tabs[0]:
        render_import_tab()
    with tabs[1]:
        render_query_tab()
    with tabs[2]:
        render_review_tab()
    with tabs[3]:
        render_sources_tab()
    with tabs[4]:
        render_export_tab()


def render_import_tab() -> None:
    _, center, _ = st.columns([0.16, 0.68, 0.16])
    with center:
        st.subheader("导入工作台")
        st.caption("先选择 PDF 文件夹；Excel 是可选补充资料，不上传也可以直接识别 PDF。")

        folder_col, button_col = st.columns([0.72, 0.28], gap="small")
        with folder_col:
            st.text_input("当前 PDF 文件夹", value=st.session_state["pdf_folder"], disabled=True)
        with button_col:
            st.write("")
            st.write("")
            if st.button("选择文件夹", use_container_width=True):
                selected = choose_pdf_folder(st.session_state["pdf_folder"])
                if selected:
                    st.session_state["pdf_folder"] = selected
                    st.session_state["pdf_folder_manual"] = selected
                    st.rerun()

        with st.expander("无法弹出选择窗口时，手动输入路径", expanded=False):
            manual_pdf_folder = st.text_input(
                "PDF 文件夹路径",
                key="pdf_folder_manual",
                help="例如：C:\\other\\UK_Order\\FOB 2026 JULY PRICE LIST",
            )
            if st.button("应用手动路径", use_container_width=True):
                st.session_state["pdf_folder"] = manual_pdf_folder
                st.session_state["pdf_folder_manual"] = manual_pdf_folder
                st.rerun()

        uploaded_excels = st.file_uploader(
            "可选 Excel 文件（可多选）",
            type=["xlsx", "xlsm", "xls"],
            accept_multiple_files=True,
            help="可上传 FOB、EZ-LIVING、Sterling、FV 等业务价格表；不上传也可以继续。",
        )
        clear_existing = st.checkbox(
            "导入前清空旧数据",
            value=True,
            help="建议保持勾选，避免新旧资料混在一起。取消勾选时，新数据会追加到现有数据库。",
        )
        action_col, preview_col = st.columns(2, gap="small")
        start = action_col.button("开始识别并汇总", type="primary", use_container_width=True)
        preview = preview_col.button("先扫描文件名", use_container_width=True)

        if preview:
            show_preview(st.session_state["pdf_folder"])
        if start:
            run_import(st.session_state["pdf_folder"], uploaded_excels, clear_existing)


def choose_pdf_folder(initial_folder: str) -> str | None:
    selected = choose_folder_with_powershell(initial_folder)
    if selected:
        return selected
    st.warning("没有打开文件夹选择窗口。可以展开“手动输入路径”后粘贴 PDF 文件夹路径。")
    return None


def choose_folder_with_powershell(initial_folder: str) -> str | None:
    initial = initial_folder if initial_folder and Path(initial_folder).exists() else str(ROOT)
    initial = initial.replace("'", "''")
    script = rf"""
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = '选择 PDF 文件夹'
$dialog.SelectedPath = '{initial}'
$dialog.ShowNewFolderButton = $false
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $dialog.SelectedPath
}}
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-STA", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
            check=False,
        )
    except Exception:
        return None
    selected = result.stdout.strip()
    return selected if selected else None


def show_preview(pdf_folder: str) -> None:
    try:
        rows = preview_pdf_folder(pdf_folder)
    except Exception as exc:  # noqa: BLE001
        st.error(f"扫描失败：{exc}")
        st.info("请确认选择的是已经解压后的 PDF 文件夹，而不是 zip 压缩包。")
        return
    st.success(f"扫描完成，共找到 {len(rows)} 个 PDF。")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def run_import(pdf_folder: str, uploaded_excels: list | None, clear_existing: bool) -> None:
    excel_files = save_uploaded_excels(uploaded_excels or [])
    progress = st.progress(0)
    status = st.empty()
    status.write("正在准备导入，请稍候...")

    def progress_callback(index: int, total: int, name: str) -> None:
        progress.progress(index / max(total, 1))
        status.write(f"正在处理：{name}")

    try:
        stats = start_import(
            pdf_folder=pdf_folder,
            excel_files=excel_files,
            clear_existing=clear_existing,
            progress_callback=progress_callback,
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"导入失败：{exc}")
        st.info("请先用“先扫描文件名”确认 PDF 文件夹是否正确；如果上传了 Excel，也请确认文件没有被其他程序占用。")
        return

    progress.progress(1.0)
    status.write("导入完成")
    st.success(
        f"已导入 {stats['pdf_files']} 个 PDF、{stats['excel_files']} 个 Excel，生成 {stats['price_rows']:,} 行价格数据。"
    )
    if stats.get("errors"):
        st.warning("部分文件未能导入，下面是需要查看的错误信息。")
        st.dataframe(pd.DataFrame({"error": stats["errors"]}), use_container_width=True, hide_index=True)


def save_uploaded_excels(uploaded_excels: list) -> list[str]:
    if not uploaded_excels:
        return []
    upload_dir = ROOT / "temp" / "uploaded_excels"
    upload_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for uploaded in uploaded_excels:
        safe_name = Path(uploaded.name).name
        path = upload_dir / safe_name
        path.write_bytes(uploaded.getvalue())
        paths.append(str(path))
    return paths


def render_query_tab() -> None:
    st.caption("按条件查询已导入的价格。留空表示不过滤。")
    filters = render_filters(prefix="query")
    rows = get_prices(filters=filters, limit=1000)
    st.session_state["last_filters"] = filters
    st.caption(f"当前显示 {len(rows):,} 行，最多显示 1,000 行")
    render_price_table(rows)


def render_review_tab() -> None:
    st.caption("这里集中显示建议人工确认的数据，方便回看来源文件。")
    filters = render_filters(prefix="review")
    filters["needs_review"] = True
    rows = get_prices(filters=filters, limit=1000)
    st.caption(f"待复核 {len(rows):,} 行，最多显示 1,000 行")
    render_price_table(rows)


def render_sources_tab() -> None:
    sources = get_table("source_files", limit=1000)
    raw_pdf = get_table("pdf_extract_raw", limit=300)
    st.subheader("导入日志")
    st.caption("查看每个来源文件是否导入成功，以及导入了多少行。")
    st.dataframe(pd.DataFrame(sources), use_container_width=True, hide_index=True)
    st.subheader("PDF 原始抽取预览")
    st.caption("这里保留 PDF 原始识别内容，便于排查价格是否被拆行或错列。")
    st.dataframe(pd.DataFrame(raw_pdf), use_container_width=True, hide_index=True)


def render_export_tab() -> None:
    st.caption("导出文件会保存到 output 文件夹，也可以在页面上直接下载。")
    use_current_filter = st.checkbox("按当前查询条件导出", value=True)
    filters = st.session_state.get("last_filters", {}) if use_current_filter else {}
    if st.button("导出 Excel", type="primary"):
        try:
            path = export_current(filters=filters)
            st.success(f"导出完成：{path}")
            with open(path, "rb") as handle:
                st.download_button(
                    "下载导出文件",
                    data=handle,
                    file_name=Path(path).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def render_filters(prefix: str) -> dict:
    first, second, third, fourth = st.columns([0.28, 0.24, 0.24, 0.24])
    keyword = first.text_input("关键词", key=f"{prefix}_keyword")
    product_code = second.text_input("Product Code", key=f"{prefix}_product_code")
    tier = third.text_input("Tier", key=f"{prefix}_tier")
    size = fourth.text_input("Size", key=f"{prefix}_size")

    fifth, sixth, seventh, eighth = st.columns(4)
    supplier = fifth.text_input("Supplier", key=f"{prefix}_supplier")
    currency = sixth.text_input("Currency", key=f"{prefix}_currency")
    cover_range = seventh.text_input("Cover Range", key=f"{prefix}_cover_range")
    source_type = eighth.selectbox("Source Type", ["", "PDF", "FOB_EXCEL", "EZ_EXCEL", "CIF_EXCEL", "FV_EXCEL"], key=f"{prefix}_source_type")

    return {
        "keyword": keyword.strip(),
        "product_code": product_code.strip(),
        "tier": tier.strip(),
        "size": size.strip(),
        "supplier": supplier.strip(),
        "currency": currency.strip(),
        "cover_range": cover_range.strip(),
        "source_type": source_type.strip(),
    }


def render_price_table(rows: list[dict]) -> None:
    if not rows:
        st.info("暂无数据")
        return
    df = pd.DataFrame(rows)
    preferred = [
        "product_code",
        "product_name",
        "supplier",
        "version",
        "price_basis",
        "currency",
        "section",
        "tier",
        "cover_range",
        "cover_type",
        "size",
        "price",
        "source_type",
        "source_file",
        "page",
        "needs_review",
        "review_reason",
    ]
    columns = [col for col in preferred if col in df.columns]
    st.dataframe(df[columns], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
