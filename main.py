import flet as ft
import requests
import json
import os

DATA_FILE = "mobile_dict_data.json"

def main(page: ft.Page):
    # --- 1. 页面基础设置 ---
    page.title = "智能词典"
    
    # 强制在电脑预览时锁定为手机屏幕比例
    page.window_width = 420
    page.window_height = 800
    page.window_resizable = False  # 在电脑上禁止缩放，锁定手机比例
    
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.padding = 0
    page.spacing = 0

    # --- 2. 本地数据处理 ---
    history_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                history_data = json.load(f).get("history", [])
        except:
            pass

    def save_data():
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"history": history_data[:50]}, f, ensure_ascii=False)

    # 递归提取纯文本
    def extract_text(node):
        if isinstance(node, str): return node
        elif isinstance(node, dict): return node.get('#text', '')
        elif isinstance(node, list): return "".join(extract_text(x) for x in node)
        return str(node)

    # --- 3. 定义 UI 控件 ---
    search_input = ft.TextField(
        hint_text="输入中文或英文...", 
        expand=True, 
        border_radius=10,
        color=ft.Colors.BLACK87,  # 输入文字颜色：深黑
        hint_style=ft.TextStyle(color=ft.Colors.BLACK38),  # 占位文字：深灰
        bgcolor=ft.Colors.WHITE,  # 输入框背景：纯白
        border_color=ft.Colors.BLUE_300  # 边框：柔和蓝
    )
    
    result_view = ft.Column(scroll="auto", expand=True, spacing=15)
    history_list = ft.Column(scroll="auto", expand=True, spacing=10)

    # 查词页面
    search_page = ft.Column([
        ft.Row([search_input, ft.ElevatedButton("翻译", on_click=lambda e: execute_search(search_input.value))]),
        result_view
    ], expand=True)

    # 历史页面
    history_page = ft.Column([
        ft.Row([
            ft.Text("查询历史", size=22, weight="bold", color=ft.Colors.BLUE_GREY_900),
            ft.TextButton("清空历史", on_click=lambda e: clear_history())
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        history_list
    ], expand=True)

    # 主内容容器
    main_content = ft.Container(content=search_page, expand=True, padding=20)

    # --- 4. 核心查词与例句逻辑 ---
    def execute_search(word):
        word = word.strip()
        if not word: return
        
        result_view.controls.clear()
        result_view.controls.append(ft.Text("正在查询...", color=ft.Colors.BLUE))
        page.update()

        try:
            url = f"http://dict.youdao.com/jsonapi?q={word}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            result_view.controls.clear()
            word_title = word
            
            # 单词标题显示
            result_view.controls.append(
                ft.Container(
                    content=ft.Text(word_title, size=30, weight="bold", color=ft.Colors.BLUE_900),
                    padding=10
                )
            )

            # 1. 解析释义
            trans_list = []
            if "ec" in data:
                for tr in data["ec"]["word"][0].get("trs", []):
                    trans_list.append(extract_text(tr["tr"][0]["l"]["i"]))
            elif "ce" in data:
                for tr in data["ce"]["word"][0].get("trs", []):
                    trans_list.append(extract_text(tr["tr"][0]["l"]["i"]))
            elif "fanyi" in data:
                trans_list.append(data["fanyi"]["tran"])

            # 渲染释义卡片
            if trans_list:
                meaning_col = ft.Column([ft.Text("📖 详细释义", size=18, weight="bold", color=ft.Colors.BLUE_700)])
                for t in trans_list:
                    if t.strip():
                        meaning_col.controls.append(ft.Text(f"• {t}", size=16, color=ft.Colors.BLACK87))
                
                result_view.controls.append(
                    ft.Container(
                        content=meaning_col, 
                        bgcolor=ft.Colors.WHITE, 
                        padding=15, 
                        border_radius=10
                    )
                )

            # 2. 解析并清洗例句中的 HTML 标签
            if "blng_sents_part" in data:
                sents = data["blng_sents_part"].get("sentence-pair", [])[:3] # 获取前 3 个例句
                if sents:
                    sents_col = ft.Column([
                        ft.Text("📝 实用例句", size=18, weight="bold", color=ft.Colors.BLUE_700),
                        ft.Container(height=5) # 间距
                    ])
                    
                    for idx, sent in enumerate(sents):
                        eng = sent.get("sentence-eng", "")
                        chn = sent.get("sentence-translation", "")
                        
                        # 【已修复】：利用字符串替换，彻底清洗掉英文句子中残留的 <b> 和 </b> 网页高亮标签
                        clean_eng = eng.replace("<b>", "").replace("</b>", "")
                        
                        sents_col.controls.append(
                            ft.Column([
                                ft.Text(f"{idx+1}. {clean_eng}", size=15, weight="bold", color=ft.Colors.BLACK87),
                                ft.Text(chn, size=14, color=ft.Colors.GREY_700),
                                ft.Container(height=5) # 例句之间的微小间距
                            ], spacing=2)
                        )
                        
                    # 渲染例句卡片
                    result_view.controls.append(
                        ft.Container(
                            content=sents_col,
                            bgcolor=ft.Colors.WHITE,
                            padding=15,
                            border_radius=10
                        )
                    )

            # 保存历史
            if word_title in history_data:
                history_data.remove(word_title)
            history_data.insert(0, word_title)
            save_data()

        except Exception as e:
            result_view.controls.clear()
            result_view.controls.append(ft.Text("查询失败，请检查拼写或网络。", color=ft.Colors.RED))
        
        page.update()

    # --- 5. 历史记录逻辑 ---
    def refresh_history():
        history_list.controls.clear()
        for w in history_data:
            item = ft.Container(
                content=ft.Text(w, size=16, color=ft.Colors.BLACK87),
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                on_click=lambda e, word=w: search_from_history(word)
            )
            history_list.controls.append(item)

    def search_from_history(word):
        search_input.value = word
        switch_tab(0)
        execute_search(word)

    def clear_history():
        history_data.clear()
        save_data()
        refresh_history()
        page.update()

    # --- 6. 页面切换导航 ---
    def switch_tab(index):
        if index == 0:
            main_content.content = search_page
        else:
            refresh_history()
            main_content.content = history_page
        page.update()

    bottom_nav = ft.Container(
        content=ft.Row([
            ft.TextButton("🔍 查词翻译", expand=True, on_click=lambda e: switch_tab(0)),
            ft.TextButton("🕒 查询历史", expand=True, on_click=lambda e: switch_tab(1)),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        bgcolor=ft.Colors.WHITE,
        padding=10
    )

    # 整体装载
    page.add(
        ft.Column([
            main_content,
            bottom_nav
        ], expand=True, spacing=0)
    )

if __name__ == "__main__":
    ft.app(target=main)