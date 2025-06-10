import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from tkcalendar import Calendar
import threading
import random
from win10toast import ToastNotifier

toaster = ToastNotifier()

DATA_FILE = "schedule_data.json"
# 색상 선택지에 사용할 색상 리스트
COLORS = ["blue", "green", "red", "orange", "purple", "brown", "gray", "cyan", "magenta"]


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_event_to_calendar(date: str, title: str, time: str = "", color: str = "blue", pinned: bool = False):
    data = load_data()
    if date not in data:
        data[date] = {"events": [], "checklist": []}
    data[date]["events"].append({
        "title": title,
        "time": time,
        "color": color,
        "pinned": pinned
    })
    save_data(data)

def check_alarms():
    def alert_thread():
        now = datetime.now()
        data = load_data()
        for date_str, content in data.items():
            for event in content.get("events") or []:
                event_time = event.get("time", "")
                if event_time:
                    try:
                        date_time_str = f"{date_str} {event_time.split('~')[0].strip()}"
                        event_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
                        diff_sec = (event_dt - now).total_seconds()
                        if 0 <= diff_sec <= 7200:
                            toaster.show_toast("⏰ 임박한 일정!", f"{event['title']} - {date_time_str}", duration=10)
                        elif 0 <= diff_sec <= 86400:
                            toaster.show_toast("📅 다가오는 일정", f"{event['title']} - {date_time_str}", duration=10)
                    except:
                        pass
    threading.Thread(target=alert_thread, daemon=True).start()

def launch_calendar_viewer():
    root = tk.Toplevel()
    root.title("📅 Plan Man 일정 관리")
    root.geometry("900x700")
    root.attributes("-topmost", True)
    root.after(500, lambda: root.attributes("-topmost", False))

    data = load_data()

    def get_selected_date():
        return cal.get_date()
    
    def open_event_dialog(date, event_info=None):
        dialog = tk.Toplevel(root)
        is_new_event = event_info is None
        dialog.title("일정 추가" if is_new_event else "일정 수정")
        dialog.geometry("400x480")
        dialog.resizable(False, False)

        result = {}

        title_var = tk.StringVar(value=event_info.get('title', '') if event_info else "")
        time_var = tk.StringVar(value=event_info.get('time', '') if event_info else "")
        color_var = tk.StringVar(value=event_info.get('color', COLORS[0]) if event_info else COLORS[0])
        pinned_var = tk.BooleanVar(value=event_info.get('pinned', False) if event_info else False)
        repeat_var = tk.BooleanVar(value=False)

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        info_frame = ttk.LabelFrame(main_frame, text="일정 정보")
        info_frame.pack(fill=tk.X, pady=5)
        ttk.Label(info_frame, text="제목:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(info_frame, textvariable=title_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(info_frame, text="시간:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(info_frame, textvariable=time_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        color_frame = ttk.LabelFrame(main_frame, text="색상 선택 (하나만 선택 가능)")
        color_frame.pack(fill=tk.X, pady=5)
        
        num_columns = 3
        for i, color in enumerate(COLORS):
            row = i // num_columns
            col = i % num_columns
            rb = ttk.Radiobutton(color_frame, text=color, variable=color_var, value=color)
            rb.grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)

        color_help_text = "참고: 날짜 칸의 배경색은 '📌고정'된 일정의 색상이 최우선으로 적용됩니다."
        ttk.Label(main_frame, text=color_help_text, font=("TkDefaultFont", 8, "italic")).pack(anchor=tk.W, padx=5)

        option_frame = ttk.LabelFrame(main_frame, text="추가 옵션")
        option_frame.pack(fill=tk.X, pady=10)
        ttk.Checkbutton(option_frame, text="📌 중요 일정으로 고정", variable=pinned_var).pack(anchor=tk.W, padx=5)
        if is_new_event:
            ttk.Checkbutton(option_frame, text="🔁 매주 반복", variable=repeat_var).pack(anchor=tk.W, padx=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        def on_ok():
            if not title_var.get().strip():
                messagebox.showwarning("입력 오류", "일정 제목을 입력해야 합니다.", parent=dialog)
                return
            
            result.update({
                "ok": True,
                "title": title_var.get(),
                "time": time_var.get(),
                "color": color_var.get(),
                "pinned": pinned_var.get(),
                "repeat": repeat_var.get()
            })
            dialog.destroy()

        def on_cancel():
            result["ok"] = False
            dialog.destroy()

        ttk.Button(btn_frame, text="확인", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="취소", command=on_cancel).pack(side=tk.RIGHT)
        
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.transient(root)
        dialog.grab_set()
        root.wait_window(dialog)
        
        return result

    def update_calendar_colors():
        cal.calevent_remove('all')
        defined_colors = set()
        for date_str, content in data.items():
            events = content.get("events", [])
            if events:
                target_event = next((e for e in events if e.get("pinned")), events[0])
                color = target_event.get("color")
                if color:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                        color_tag = f"color_{color}"
                        cal.calevent_create(date_obj, '', tags=[color_tag])
                        if color not in defined_colors:
                            cal.tag_config(color_tag, background=color)
                            defined_colors.add(color)
                    except Exception as e:
                        print(f"Could not apply color '{color}' for {date_str}: {e}")

    def refresh_all(event=None):
        date = get_selected_date()
        events = data.get(date, {}).get("events") or []
        checklist = data.get(date, {}).get("checklist") or []
        event_listbox.delete(0, tk.END)
        if not events:
            event_listbox.insert(tk.END, "🗓️ 등록된 일정이 없습니다.")
        else:
            sorted_events = sorted(events, key=lambda e: (e.get("time", ""), e.get("title")))
            for e in sorted_events:
                mark = "📌 " if e.get("pinned") else ""
                display = f"{mark}{e.get('title')} [{e.get('time', '시간 미지정')}]"
                event_listbox.insert(tk.END, display)
        checklist_frame_clear()
        for idx, item in enumerate(checklist):
            item_frame = tk.Frame(checklist_frame)
            item_frame.pack(fill='x', expand=True, pady=2)
            var = tk.BooleanVar(value=item.get("done", False))
            cb = tk.Checkbutton(item_frame, text=item["task"], variable=var,
                                command=lambda i=idx, v=var: toggle_check_item(get_selected_date(), i, v))
            cb.pack(side=tk.LEFT, anchor="w")
            if item.get("done", False):
                delete_button = ttk.Button(item_frame, text="삭제",
                                           command=lambda i=idx: delete_check_item(get_selected_date(), i))
                delete_button.pack(side=tk.RIGHT, padx=5)

    def add_event():
        date = get_selected_date()
        dialog_result = open_event_dialog(date)

        if dialog_result.get("ok"):
            add_event_to_calendar(date, dialog_result["title"], dialog_result["time"], dialog_result["color"], dialog_result["pinned"])
            if dialog_result.get("repeat"):
                repeat_weekly(date, dialog_result["title"], dialog_result["time"], dialog_result["color"], dialog_result["pinned"])
            data.clear()
            data.update(load_data())
            refresh_all()
            update_calendar_colors()

    def edit_event():
        date = get_selected_date()
        selected_indices = event_listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        sorted_events = sorted(data.get(date, {}).get("events", []), key=lambda e: (e.get("time", ""), e.get("title")))
        if idx >= len(sorted_events): return
        event_to_edit = sorted_events[idx]
        original_event = next((e for e in data[date]["events"] if e == event_to_edit), None)
        if not original_event: return

        dialog_result = open_event_dialog(date, event_info=original_event)

        if dialog_result.get("ok"):
            original_event["title"] = dialog_result["title"]
            original_event["time"] = dialog_result["time"]
            original_event["color"] = dialog_result["color"]
            original_event["pinned"] = dialog_result["pinned"]
            save_data(data)
            refresh_all()
            update_calendar_colors()

    def delete_event():
        date = get_selected_date()
        selected_indices = event_listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        sorted_events = sorted(data.get(date, {}).get("events", []), key=lambda e: (e.get("time", ""), e.get("title")))
        if idx >= len(sorted_events): return
        
        event_to_delete = sorted_events[idx]
        data[date]["events"].remove(event_to_delete)
        if not data[date]["events"] and not data[date]["checklist"]:
            del data[date]
        save_data(data)
        refresh_all()
        update_calendar_colors()

    def repeat_weekly(date, title, time, color, pinned):
        base_date = datetime.strptime(date, "%Y-%m-%d")
        for i in range(1, 5):
            next_date = (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d")
            add_event_to_calendar(next_date, title, time, color, pinned)

    def add_check_item():
        date = get_selected_date()
        task = simpledialog.askstring("체크리스트", "할 일:", parent=root)
        if not task: return
        if date not in data:
            data[date] = {"events": [], "checklist": []}
        data[date]["checklist"].append({"task": task, "done": False})
        save_data(data)
        refresh_all()

    def toggle_check_item(date, index, var):
        if date in data and index < len(data[date]["checklist"]):
            data[date]["checklist"][index]["done"] = var.get()
            save_data(data)
            refresh_all()

    def delete_check_item(date, index):
        if date in data and index < len(data[date]["checklist"]):
            del data[date]["checklist"][index]
            save_data(data)
            refresh_all()

    def checklist_frame_clear():
        for widget in checklist_frame.winfo_children():
            widget.destroy()

    cal = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd",
                   year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    # >>>>>>>> 수정된 부분: fill='both'와 expand=True 옵션 추가 <<<<<<<<
    cal.pack(pady=10, fill="both", expand=True, padx=10)
    cal.bind("<<CalendarSelected>>", refresh_all)

    # 일정 리스트와 체크리스트는 창 크기가 변해도 세로로 늘어나지 않도록 expand=False (기본값) 유지
    event_listbox = tk.Listbox(root, width=80, height=10)
    event_listbox.pack(pady=5, fill="x", padx=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    ttk.Button(btn_frame, text="➕ 일정 추가", command=add_event).grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="✏️ 수정", command=edit_event).grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="❌ 삭제", command=delete_event).grid(row=0, column=2, padx=5)

    tk.Label(root, text="✅ 체크리스트", font=("Arial", 14)).pack(pady=(10,0))
    checklist_frame = tk.Frame(root)
    checklist_frame.pack(fill="x", padx=10)

    ttk.Button(root, text="➕ 체크 항목 추가", command=add_check_item).pack(pady=10)

    refresh_all()
    update_calendar_colors()
    root.mainloop()

check_alarms()