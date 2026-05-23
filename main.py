import flet as ft
import requests

def main(page: ft.Page):
    # --- 1. 页面基础设置 ---
    page.title = "智能词典"
    page.window_width = 420
    page.window_height = 800
    page.window_resizable = False  
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.padding = 20
    page.spacing = 10

    # --- 2. 本地数据处理 ---
    history_data = []
    try:
        history_data = page.client_storage.get("history") or []
    except:
        pass

    def save_data():
        try:
            page.client_storage.set("history", history_data[:50])
        except:
            pass

    # 递归提取纯文本
    def extract_text(node):
        if isinstance(node, str): return node
        elif isinstance(node, dict): return node.get('#text', '')
        elif isinstance(node, list): return "".join(extract_text(x) for x in node)
        return str(node)

    # --- 3. 定义 UI 基础控件 ---
    # 【修改点】：删去了 expand=True，固定宽度为 250，保证在任何手机屏幕上都不会撑破边缘
    search_input = ft.TextField(
        hint_text="输入中文或英文...", 
        width=250,  
        color=ft.Colors.BLACK87,  
        hint_style=ft.TextStyle(color=ft.Colors.BLACK38),  
        bgcolor=ft.Colors.WHITE,  
        border_color=ft.Colors.BLUE_300,
        border_radius=10
    )
    
    result_view = ft.Column(spacing=15, scroll="auto")
    history_list = ft.Column(spacing=10, scroll="auto")

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

            # 解析释义
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

            # 解析并清洗例句中的 HTML 标签
            if "blng_sents_part" in data:
                sents = data["blng_sents_part"].get("sentence-pair", [])[:3] 
                if sents:
                    sents_col = ft.Column([
                        ft.Text("📝 实用例句", size=18, weight="bold", color=ft.Colors.BLUE_700),
                        ft.Container(height=5) 
                    ])
                    
                    for idx, sent in enumerate(sents):
                        eng = sent.get("sentence-eng", "")
                        chn = sent.get("sentence-translation", "")
                        clean_eng = eng.replace("<b>", "").replace("</b>", "")
                        
                        sents_col.controls.append(
                            ft.Column([
                                ft.Text(f"{idx+1}. {clean_eng}", size=15, weight="bold", color=ft.Colors.BLACK87),
                                ft.Text(chn, size=14, color=ft.Colors.GREY_700),
                                ft.Container(height=5) 
                            ], spacing=2)
                        )
                        
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
        show_search_page()
        execute_search(word)

    def clear_history():
        history_data.clear()
        save_data()
        refresh_history()
        page.update()

    # --- 6. 极简安全路由切换（彻底回退到上一个正常版的无嵌套架构） ---
    def show_search_page():
        page.controls.clear()
        page.add(
            # 【修改点】：直接通过 Row 居中对齐，让输入框和翻译按钮整体往中间挪，两边自然空出安全距离
            ft.Row([
                search_input, 
                ft.ElevatedButton("翻译", on_click=lambda e: execute_search(search_input.value))
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Container(content=result_view, expand=True), 
            bottom_nav
        )
        page.update()

    def show_history_page():
        refresh_history()
        page.controls.clear()
        page.add(
            ft.Row([
                ft.Text("查询历史", size=22, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.TextButton("清空历史", on_click=lambda e: clear_history())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=history_list, expand=True), 
            bottom_nav
        )
        page.update()

    # 【已回退】：完全恢复到上一个正常版本的导航栏，不做任何多余的 margin 改动
    bottom_nav = ft.Container(
        content=ft.Row([
            ft.TextButton("🔍 查词翻译", expand=True, on_click=lambda e: show_search_page()),
            ft.TextButton("🕒 查询历史", expand=True, on_click=lambda e: show_history_page()),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        bgcolor=ft.Colors.WHITE,
        padding=10
    )

    # 启动默认进入查词页
    show_search_page()

if __name__ == "__main__":
    ft.app(target=main)
