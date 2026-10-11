import flet as ft
import asyncio
import random
from core.loader import load_subjects, load_subject, load_pretest
from core.scoring import calculate_score, grade_label


async def main(page: ft.Page):
    page.title = "Study App"
    page.window_width = 800
    page.window_height = 800
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    subjects = load_subjects()
    user = {"name": "Nathan"}

    # ============================================================
    #                       PROFILE DRAWER
    # ============================================================
    async def go_profile(e):
        await page.close_drawer()
        show_profile()

    async def go_statistics(e):
        await page.close_drawer()
        show_statistics()

    async def go_recommendations(e):
        await page.close_drawer()
        show_recommendations()

    async def exit_app(e):
        await page.window.destroy()

    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.CircleAvatar(
                        content=ft.Text("N", size=24),
                        radius=30,
                        bgcolor=ft.Colors.BLUE_400,
                    ),
                    ft.Text(user["name"], size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Joined Sep 2026", size=12, color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Divider(),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PERSON),
                title=ft.Text("Profile"),
                on_click=go_profile,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.BAR_CHART),
                title=ft.Text("Statistics"),
                on_click=go_statistics,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LIGHTBULB),
                title=ft.Text("Recommendations"),
                on_click=go_recommendations,
            ),
            ft.Divider(),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.EXIT_TO_APP),
                title=ft.Text("Exit"),
                on_click=exit_app,
            ),
        ],
    )
    page.drawer = drawer

    async def open_drawer(e):
        try:
            await page.show_drawer()
        except Exception:
            await page.close_drawer()

    # ============================================================
    #                        TOP BAR
    # ============================================================
    def top_bar(title="Study App", show_back=False, back_fn=None):
        leading = (
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: back_fn())
            if show_back else
            ft.Icon(ft.Icons.MENU_BOOK, size=24)
        )
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=15, vertical=10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row([
                leading,
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, expand=True),
                ft.IconButton(
                    ft.Icons.ACCOUNT_CIRCLE,
                    icon_size=32,
                    on_click=open_drawer,
                ),
            ]),
        )

    # ============================================================
    #                       HOME SCREEN
    # ============================================================
    def show_home():
        page.clean()

        def feature_card(icon, title, subtitle, button_text, on_click):
            return ft.Container(
                padding=20,
                margin=ft.Margin.symmetric(vertical=6),
                border_radius=12,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                content=ft.Column([
                    ft.Row([
                        ft.Text(icon, size=28),
                        ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Text(subtitle, size=13, color=ft.Colors.GREY),
                    ft.Row([
                        ft.Button(content=button_text, on_click=on_click),
                    ], alignment=ft.MainAxisAlignment.END),
                ], spacing=8),
            )

        page.add(
            top_bar("📚 Study App"),
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text(f"Welcome back, {user['name']}.", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text("What would you like to do today?", size=14, color=ft.Colors.GREY),
                    ft.Divider(),

                    feature_card(
                        "🧠", "Cognitive Test",
                        "Verbal, numerical, logical, and spatial reasoning.",
                        "Start →",
                        lambda e: show_stub("Cognitive Test"),
                    ),
                    feature_card(
                        "📖", "Curriculum Test",
                        "Study and test school subjects.",
                        "Choose Subject →",
                        lambda e: show_subject_menu(),
                    ),
                    feature_card(
                        "💗", "EQ Assessment",
                        "Measure your emotional intelligence.",
                        "Start →",
                        lambda e: show_stub("EQ Assessment"),
                    ),
                    feature_card(
                        "📚", "Lessons",
                        "Read up on subjects before testing.",
                        "Browse →",
                        lambda e: show_stub("Lessons"),
                    ),
                    feature_card(
                        "📊", "My Progress",
                        "See your scores and trends over time.",
                        "View →",
                        lambda e: show_statistics(),
                    ),
                ]),
            ),
        )
        page.update()

    # ============================================================
    #                       STUB SCREEN
    # ============================================================
    def show_stub(name):
        page.clean()
        page.add(
            top_bar(name, show_back=True, back_fn=show_home),
            ft.Container(
                padding=40,
                content=ft.Column([
                    ft.Text("🚧", size=64),
                    ft.Text(f"{name}", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Coming soon.", size=16, color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        )
        page.update()

    # ============================================================
    #                       PROFILE PAGE
    # ============================================================
    def show_profile():
        page.clean()
        page.add(
            top_bar("Profile", show_back=True, back_fn=show_home),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text("N", size=36),
                            radius=48,
                            bgcolor=ft.Colors.BLUE_400,
                        ),
                        ft.Column([
                            ft.Text(user["name"], size=26, weight=ft.FontWeight.BOLD),
                            ft.Text("Student", size=14, color=ft.Colors.GREY),
                        ], spacing=2),
                    ], spacing=20),
                    ft.Divider(),
                    ft.Text("Account details will appear here.", size=14, color=ft.Colors.GREY),
                ]),
            ),
        )
        page.update()

    # ============================================================
    #                     STATISTICS PAGE
    # ============================================================
    def show_statistics():
        page.clean()
        page.add(
            top_bar("Statistics", show_back=True, back_fn=show_home),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Text("📊", size=64),
                    ft.Text("Your Stats", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Past test scores and trends will appear here once we add CSV logging.",
                            size=14, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        )
        page.update()

    # ============================================================
    #                   RECOMMENDATIONS PAGE
    # ============================================================
    def show_recommendations():
        page.clean()
        page.add(
            top_bar("Recommendations", show_back=True, back_fn=show_home),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Text("💡", size=64),
                    ft.Text("Personalized Suggestions", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Based on your test results, you'll see study recommendations here.",
                            size=14, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        )
        page.update()

    # ============================================================
    #                  CURRICULUM SUBJECT MENU
    # ============================================================
    def show_subject_menu():
        page.clean()
        content = ft.Column([
            ft.Text("📖 Choose a Subject", size=26, weight=ft.FontWeight.BOLD),
            ft.Text("Tap a subject to begin a test.", size=14, color=ft.Colors.GREY),
            ft.Divider(),
        ])

        for subject in subjects:
            count = len(load_subject(subject["id"]))
            content.controls.append(
                ft.Button(
                    content=ft.Row([
                        ft.Text(subject["icon"], size=22),
                        ft.Text(f"{subject['name']}  ({count})", size=16),
                    ]),
                    width=650,
                    height=55,
                    disabled=(count == 0),
                    on_click=lambda e, s=subject: start_subject_test(s),
                )
            )

        content.controls.append(
            ft.Button(
                content="🧠 Take Full Pretest (10 per subject)",
                width=650,
                height=55,
                on_click=lambda e: start_pretest(),
            )
        )

        page.add(
            top_bar("Curriculum", show_back=True, back_fn=show_home),
            ft.Container(padding=20, content=content),
        )
        page.update()

    # ============================================================
    #                       TEST STARTERS
    # ============================================================
    def start_pretest():
        questions = load_pretest(per_subject=10)
        if not questions:
            show_stub("Pretest — no questions available")
            return
        fake_subject = {"id": "pretest", "name": "Pretest", "icon": "🧠"}
        run_quiz(fake_subject, questions, is_pretest=True)

    def start_subject_test(subject):
        questions = load_subject(subject["id"])
        if not questions:
            show_stub(f"{subject['name']} — no questions yet")
            return
        run_quiz(subject, questions, is_pretest=False)

    # ============================================================
    #                        QUIZ ENGINE
    # ============================================================
    def run_quiz(subject, questions, is_pretest=False):
        state = {"index": 0, "correct": 0, "by_type": {}, "by_subject": {}}

        progress_text = ft.Text("", size=14, color=ft.Colors.GREY)
        question_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD)
        choices_column = ft.Column(spacing=10)
        feedback_text = ft.Text("", size=16)

        def request_exit(e):
            def close_dialog(confirmed: bool):
                confirm_dialog.open = False
                page.update()
                if confirmed:
                    if is_pretest:
                        show_home()
                    else:
                        show_subject_menu()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cancel this test?"),
                content=ft.Text("Your progress on this test will be lost. Are you sure?"),
                actions=[
                    ft.TextButton("Keep Testing", on_click=lambda e: close_dialog(False)),
                    ft.TextButton("Yes, Cancel", on_click=lambda e: close_dialog(True)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(confirm_dialog)
            confirm_dialog.open = True
            page.update()

        back_button = ft.TextButton(
            content=ft.Row([ft.Text("←", size=18), ft.Text("Back", size=14)]),
            on_click=request_exit,
        )

        def render():
            q = questions[state["index"]]
            progress_text.value = (
                f"{subject['name']} — Question {state['index'] + 1} of {len(questions)}"
            )
            question_text.value = q["question"]
            feedback_text.value = ""
            choices_column.controls.clear()
            for choice in q["choices"]:
                choices_column.controls.append(
                    ft.Button(
                        content=choice,
                        width=600,
                        on_click=lambda e, c=choice: check(c),
                    )
                )
            page.update()

        def check(choice):
            q = questions[state["index"]]
            qtype = q.get("type", "General")
            state["by_type"].setdefault(qtype, {"correct": 0, "total": 0})
            state["by_type"][qtype]["total"] += 1

            if is_pretest:
                subj_name = q.get("_subject_name", "Unknown")
                state["by_subject"].setdefault(subj_name, {"correct": 0, "total": 0})
                state["by_subject"][subj_name]["total"] += 1

            if choice == q["answer"]:
                state["correct"] += 1
                state["by_type"][qtype]["correct"] += 1
                if is_pretest:
                    subj_name = q.get("_subject_name", "Unknown")
                    state["by_subject"][subj_name]["correct"] += 1
                feedback_text.value = "✅ Correct!"
                feedback_text.color = ft.Colors.GREEN
            else:
                feedback_text.value = f"❌ Wrong. Answer: {q['answer']}\n{q['explanation']}"
                feedback_text.color = ft.Colors.RED

            for btn in choices_column.controls:
                btn.disabled = True
            page.update()

            async def advance():
                await asyncio.sleep(1.5)
                state["index"] += 1
                if state["index"] < len(questions):
                    render()
                else:
                    show_results()

            page.run_task(advance)

        def show_results():
            score = calculate_score(state["correct"], len(questions))
            label = grade_label(score)

            page.clean()
            page.add(top_bar(subject["name"], show_back=True, back_fn=show_home))

            content = ft.Column([
                ft.Text("Test Complete!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Score: {state['correct']} / {len(questions)}", size=20),
                ft.Text(f"Percentage: {score}%", size=20),
                ft.Text(f"Rating: {label}", size=20, color=ft.Colors.BLUE),
            ])

            if is_pretest and state["by_subject"]:
                content.controls.append(ft.Divider())
                content.controls.append(ft.Text("By subject:", size=18, weight=ft.FontWeight.BOLD))
                for subj_name, stats in sorted(state["by_subject"].items()):
                    pct = round(stats["correct"] / stats["total"] * 100, 1)
                    color = (
                        ft.Colors.GREEN if pct >= 70
                        else ft.Colors.ORANGE if pct >= 50
                        else ft.Colors.RED
                    )
                    content.controls.append(
                        ft.Text(f"  • {subj_name}: {stats['correct']}/{stats['total']} ({pct}%)",
                                size=14, color=color)
                    )

            if state["by_type"]:
                content.controls.append(ft.Divider())
                content.controls.append(ft.Text("By question type:", size=18, weight=ft.FontWeight.BOLD))
                for qtype, stats in sorted(state["by_type"].items()):
                    pct = round(stats["correct"] / stats["total"] * 100, 1)
                    content.controls.append(
                        ft.Text(f"  • {qtype}: {stats['correct']}/{stats['total']} ({pct}%)", size=14)
                    )

            content.controls.append(ft.Divider())
            content.controls.append(
                ft.Button(content="Back to Home", on_click=lambda e: show_home())
            )

            page.add(ft.Container(padding=20, content=content))
            page.update()

        page.clean()
        page.add(top_bar(subject["name"], show_back=True, back_fn=show_home))
        page.add(
            ft.Container(
                padding=20,
                content=ft.Column([
                    back_button,
                    ft.Divider(),
                    progress_text,
                    question_text,
                    choices_column,
                    feedback_text,
                ]),
            )
        )
        render()

    # ============================================================
    #                          START
    # ============================================================
    show_home()


ft.run(main)