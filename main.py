import flet as ft
import asyncio
import random
import json
from core.loader import (load_subjects, load_subject, load_pretest,
                          load_onboarding_pretest, load_cognitive_pool,
                          load_eq_assessment, load_licensure_exams,
                          load_licensure_exam, pick_questions)
from core.scoring import calculate_score, grade_label, calculate_iq_score, calculate_eq_score
from core import database as db
from core import recommender


async def main(page: ft.Page):
    page.title = "Study App"
    page.window_width = 800
    page.window_height = 800
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    subjects = load_subjects()

    # ============================================================
    #                    CURRENT USER STATE
    # ============================================================
    current_user = None  # dict with user data from DB, or None

    # ============================================================
    #                    HELPER: REFRESH DRAWER
    # ============================================================
    def refresh_drawer():
        nonlocal drawer
        name = current_user["name"] if current_user else "Guest"
        initial = name[0].upper() if name else "G"
        drawer.controls[0] = ft.Container(
            padding=20,
            content=ft.Column([
                ft.CircleAvatar(
                    content=ft.Text(initial, size=24),
                    radius=30,
                    bgcolor=ft.Colors.BLUE_400,
                ),
                ft.Text(name, size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Student", size=12, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
        # Update logout/login tile
        if current_user:
            drawer.controls[-2] = ft.Divider()
            drawer.controls[-1] = ft.ListTile(
                leading=ft.Icon(ft.Icons.LOGOUT),
                title=ft.Text("Logout"),
                on_click=do_logout,
            )
        else:
            drawer.controls[-2] = ft.Divider()
            drawer.controls[-1] = ft.ListTile(
                leading=ft.Icon(ft.Icons.LOGIN),
                title=ft.Text("Login / Sign Up"),
                on_click=lambda e: show_onboarding(),
            )
        page.update()

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

    async def do_logout(e):
        nonlocal current_user
        current_user = None
        refresh_drawer()
        show_home()

    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.CircleAvatar(
                        content=ft.Text("G", size=24),
                        radius=30,
                        bgcolor=ft.Colors.BLUE_400,
                    ),
                    ft.Text("Guest", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Student", size=12, color=ft.Colors.GREY),
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
                leading=ft.Icon(ft.Icons.LOGIN),
                title=ft.Text("Login / Sign Up"),
                on_click=lambda e: show_onboarding(),
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
    #                   ONBOARDING - WELCOME SCREEN
    # ============================================================
    def show_onboarding():
        page.clean()
        page.add(
            top_bar("📚 Study App"),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Text("👋 Welcome!", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Before we get started, let's gauge your baseline knowledge "
                        "with a short 10-question pretest. No pressure — it's just to "
                        "help us personalize your learning experience.",
                        size=15,
                        color=ft.Colors.GREY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=20),
                    ft.FilledButton(
                        content=ft.Row([
                            ft.Text("🧠  Start Pretest", size=16, weight=ft.FontWeight.BOLD),
                        ]),
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=30, vertical=14),
                        ),
                        on_click=lambda e: start_onboarding_pretest(),
                    ),
                    ft.TextButton(
                        content=ft.Text("Skip pretest →", size=13),
                        on_click=lambda e: show_signup(),
                    ),
                    ft.Container(height=10),
                    ft.TextButton(
                        content=ft.Text("Already have an account? Login →", size=13),
                        on_click=lambda e: show_login(),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            ),
        )
        page.update()

    # ============================================================
    #              ONBOARDING PRETEST (uses quiz engine)
    # ============================================================
    def start_onboarding_pretest():
        questions = load_onboarding_pretest()
        if not questions:
            show_stub("Pretest — no questions available")
            return
        fake_subject = {"id": "onboarding", "name": "Onboarding Pretest", "icon": "🧠"}
        run_quiz(fake_subject, questions, is_pretest=False, is_onboarding=True)

    # ============================================================
    #                   SIGNUP SCREEN
    # ============================================================
    def show_signup():
        page.clean()

        name_field = ft.TextField(label="Full Name", hint_text="Enter your name",
                                  prefix_icon=ft.Icons.PERSON, expand=True)
        email_field = ft.TextField(label="Email (optional)", hint_text="you@example.com",
                                   prefix_icon=ft.Icons.EMAIL, expand=True)
        pass_field = ft.TextField(label="Password", hint_text="At least 4 characters",
                                  prefix_icon=ft.Icons.LOCK, password=True,
                                  can_reveal_password=True, expand=True)
        error_text = ft.Text("", size=13, color=ft.Colors.RED)

        def do_signup(e):
            name = name_field.value.strip()
            email = email_field.value.strip() if email_field.value else None
            password = pass_field.value.strip() if pass_field.value else None

            if not name:
                error_text.value = "Please enter your name."
                page.update()
                return
            if not password or len(password) < 4:
                error_text.value = "Password must be at least 4 characters."
                page.update()
                return

            user = db.create_user(name, email, password)
            if user:
                nonlocal current_user
                current_user = user
                refresh_drawer()
                show_home()
            else:
                error_text.value = "Failed to create account. Email may already be in use."
                page.update()

        page.add(
            top_bar("Create Account", show_back=True, back_fn=show_onboarding),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Text("📝 Sign Up", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Create an account to save your progress and scores.",
                            size=14, color=ft.Colors.GREY),
                    ft.Container(height=15),
                    ft.Row([name_field], spacing=10),
                    ft.Row([email_field], spacing=10),
                    ft.Row([pass_field], spacing=10),
                    ft.Container(height=10),
                    error_text,
                    ft.FilledButton(
                        content=ft.Text("Create Account", size=15, weight=ft.FontWeight.BOLD),
                        on_click=do_signup,
                    ),
                    ft.TextButton(
                        content=ft.Text("Continue as Guest →", size=13),
                        on_click=lambda e: show_home(),
                    ),
                ], spacing=10),
            ),
        )
        page.update()

    # ============================================================
    #                   LOGIN SCREEN
    # ============================================================
    def show_login():
        page.clean()

        email_field = ft.TextField(label="Email", hint_text="you@example.com",
                                   prefix_icon=ft.Icons.EMAIL, expand=True)
        pass_field = ft.TextField(label="Password", hint_text="Enter your password",
                                  prefix_icon=ft.Icons.LOCK, password=True,
                                  can_reveal_password=True, expand=True)
        error_text = ft.Text("", size=13, color=ft.Colors.RED)

        def do_login(e):
            email = email_field.value.strip()
            password = pass_field.value.strip()

            if not email or not password:
                error_text.value = "Please enter both email and password."
                page.update()
                return

            user = db.login_user(email, password)
            if user:
                nonlocal current_user
                current_user = user
                refresh_drawer()
                show_home()
            else:
                error_text.value = "Invalid email or password."
                page.update()

        page.add(
            top_bar("Login", show_back=True, back_fn=show_onboarding),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Text("🔐 Login", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Sign in to continue where you left off.",
                            size=14, color=ft.Colors.GREY),
                    ft.Container(height=15),
                    ft.Row([email_field], spacing=10),
                    ft.Row([pass_field], spacing=10),
                    ft.Container(height=10),
                    error_text,
                    ft.FilledButton(
                        content=ft.Text("Login", size=15, weight=ft.FontWeight.BOLD),
                        on_click=do_login,
                    ),
                    ft.TextButton(
                        content=ft.Text("Don't have an account? Sign up →", size=13),
                        on_click=lambda e: show_signup(),
                    ),
                    ft.TextButton(
                        content=ft.Text("Continue as Guest →", size=13),
                        on_click=lambda e: show_home(),
                    ),
                ], spacing=10),
            ),
        )
        page.update()

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

        name = current_user["name"] if current_user else "Guest"

        page.add(
            top_bar("📚 Study App"),
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text(f"Welcome back, {name}.", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text("What would you like to do today?", size=14, color=ft.Colors.GREY),
                    ft.Divider(),

                    feature_card(
                        "🧠", "Cognitive Test",
                        "Verbal, numerical, logical, and spatial reasoning.",
                        "Start →",
                        lambda e: show_cognitive_test_menu(),
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
                        lambda e: start_eq_assessment(),
                    ),
                    feature_card(
                        "📚", "Lessons",
                        "Read up on subjects before testing.",
                        "Browse →",
                        lambda e: show_learning_mode(),
                    ),
                    feature_card(
                        "📝", "Mock Exam",
                        "Practice licensure and board exams.",
                        "Choose Exam →",
                        lambda e: show_mock_test_menu(),
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
    #              COGNITIVE TEST MENU
    # ============================================================
    COGNITIVE_DOMAINS = [
        {"id": "verbal", "name": "Verbal Reasoning", "icon": "🗣️", "color": ft.Colors.BLUE_50},
        {"id": "numerical", "name": "Numerical Reasoning", "icon": "🔢", "color": ft.Colors.GREEN_50},
        {"id": "logical", "name": "Logical Reasoning", "icon": "🧩", "color": ft.Colors.ORANGE_50},
        {"id": "spatial", "name": "Spatial Reasoning", "icon": "🔷", "color": ft.Colors.PURPLE_50},
    ]

    def show_cognitive_test_menu():
        page.clean()
        content = ft.Column([
            ft.Text("🧠 Cognitive Test", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Choose a domain to test, or take all four for a full IQ estimate.",
                    size=14, color=ft.Colors.GREY),
            ft.Divider(),
        ])

        for domain in COGNITIVE_DOMAINS:
            count = len(load_cognitive_pool(domain["id"]))
            content.controls.append(
                ft.Container(
                    padding=15,
                    margin=ft.Margin.only(bottom=8),
                    border_radius=10,
                    bgcolor=domain["color"],
                    content=ft.Row([
                        ft.Text(domain["icon"], size=24),
                        ft.Column([
                            ft.Text(domain["name"], size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{count} questions available", size=12, color=ft.Colors.GREY),
                        ], spacing=2),
                        ft.FilledButton(
                            content=ft.Text("Start →"),
                            on_click=lambda e, d=domain["id"]: start_cognitive_test(d),
                        ),
                    ], spacing=15),
                )
            )

        content.controls.append(
            ft.FilledButton(
                content=ft.Row([
                    ft.Text("🧠  Take Full Cognitive Test (All 4 Domains)", size=15,
                            weight=ft.FontWeight.BOLD),
                ]),
                on_click=lambda e: start_full_cognitive_test(),
            )
        )

        page.add(
            top_bar("Cognitive Test", show_back=True, back_fn=show_home),
            ft.Container(padding=20, content=content),
        )
        page.update()

    def start_cognitive_test(domain_id):
        questions = load_cognitive_pool(domain_id)
        if not questions:
            show_stub(f"{domain_id} — no questions yet")
            return
        domain_info = next(d for d in COGNITIVE_DOMAINS if d["id"] == domain_id)
        fake_subject = {"id": domain_id, "name": domain_info["name"], "icon": domain_info["icon"]}
        run_cognitive_quiz(fake_subject, questions, domain_id)

    def start_full_cognitive_test():
        all_questions = []
        domain_results = {}
        for domain in COGNITIVE_DOMAINS:
            qs = load_cognitive_pool(domain["id"])
            if qs:
                picked = random.sample(qs, min(10, len(qs)))
                all_questions.extend(picked)
        random.shuffle(all_questions)
        if not all_questions:
            show_stub("Cognitive Test — no questions available")
            return
        fake_subject = {"id": "cognitive_full", "name": "Full Cognitive Test", "icon": "🧠"}
        run_cognitive_quiz_full(fake_subject, all_questions)

    def run_cognitive_quiz(subject, questions, domain_id):
        state = {"index": 0, "correct": 0}

        progress_text = ft.Text("", size=14, color=ft.Colors.GREY)
        question_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD)
        choices_column = ft.Column(spacing=10)
        feedback_text = ft.Text("", size=16)

        def request_exit(e):
            def close_dialog(confirmed: bool):
                confirm_dialog.open = False
                page.update()
                if confirmed:
                    show_cognitive_test_menu()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cancel this test?"),
                content=ft.Text("Your progress will be lost."),
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
            progress_text.value = f"{subject['name']} — Question {state['index'] + 1} of {len(questions)}"
            question_text.value = q["question"]
            feedback_text.value = ""
            choices_column.controls.clear()
            for choice in q["choices"]:
                choices_column.controls.append(
                    ft.Button(content=choice, width=600,
                              on_click=lambda e, c=choice: check(c))
                )
            page.update()

        def check(choice):
            q = questions[state["index"]]
            if choice == q["answer"]:
                state["correct"] += 1
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
            # Map to IQ scale for single domain
            iq_result = calculate_iq_score({domain_id: score})

            # Save to DB
            if current_user:
                db.save_test_result(
                    user_id=current_user["id"],
                    test_type="cognitive",
                    subject=subject["name"],
                    correct=state["correct"],
                    total=len(questions),
                    score=score,
                    details=json.dumps({"iq_estimate": iq_result["overall"]}),
                )

            page.clean()
            page.add(top_bar(subject["name"], show_back=True, back_fn=show_cognitive_test_menu))
            content = ft.Column([
                ft.Text("Test Complete!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Score: {state['correct']} / {len(questions)}", size=20),
                ft.Text(f"Percentage: {score}%", size=20),
                ft.Text(f"Rating: {label}", size=20, color=ft.Colors.BLUE),
                ft.Container(height=10),
                ft.Text("⚠️ This is an estimate, not a clinically validated IQ test.",
                        size=12, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
            ])
            content.controls.append(ft.Divider())
            content.controls.append(
                ft.Button(content="Back to Cognitive Tests",
                          on_click=lambda e: show_cognitive_test_menu())
            )
            page.add(ft.Container(padding=20, content=content))
            page.update()

        page.clean()
        page.add(top_bar(subject["name"], show_back=True, back_fn=show_cognitive_test_menu))
        page.add(ft.Container(padding=20, content=ft.Column([
            back_button, ft.Divider(), progress_text, question_text,
            choices_column, feedback_text,
        ])))
        render()

    def run_cognitive_quiz_full(subject, questions):
        state = {"index": 0, "correct": 0, "by_domain": {}}

        progress_text = ft.Text("", size=14, color=ft.Colors.GREY)
        question_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD)
        choices_column = ft.Column(spacing=10)
        feedback_text = ft.Text("", size=16)

        # Tag questions with domain
        tagged = []
        for q in questions:
            q_copy = dict(q)
            qtype = q_copy.get("type", "")
            for d in COGNITIVE_DOMAINS:
                if qtype == d["id"].capitalize():
                    q_copy["_domain"] = d["id"]
                    break
            tagged.append(q_copy)

        def request_exit(e):
            def close_dialog(confirmed: bool):
                confirm_dialog.open = False
                page.update()
                if confirmed:
                    show_cognitive_test_menu()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cancel this test?"),
                content=ft.Text("Your progress will be lost."),
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
            q = tagged[state["index"]]
            progress_text.value = f"{subject['name']} — Question {state['index'] + 1} of {len(tagged)}"
            question_text.value = q["question"]
            feedback_text.value = ""
            choices_column.controls.clear()
            for choice in q["choices"]:
                choices_column.controls.append(
                    ft.Button(content=choice, width=600,
                              on_click=lambda e, c=choice: check(c))
                )
            page.update()

        def check(choice):
            q = tagged[state["index"]]
            domain = q.get("_domain", "unknown")
            state["by_domain"].setdefault(domain, {"correct": 0, "total": 0})
            state["by_domain"][domain]["total"] += 1

            if choice == q["answer"]:
                state["correct"] += 1
                state["by_domain"][domain]["correct"] += 1
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
                if state["index"] < len(tagged):
                    render()
                else:
                    show_results()
            page.run_task(advance)

        def show_results():
            score = calculate_score(state["correct"], len(tagged))
            label = grade_label(score)

            # Calculate domain scores
            domain_scores = {}
            for domain, stats in state["by_domain"].items():
                domain_scores[domain] = calculate_score(stats["correct"], stats["total"])

            iq_result = calculate_iq_score(domain_scores)

            # Save to DB
            if current_user:
                db.save_test_result(
                    user_id=current_user["id"],
                    test_type="cognitive_full",
                    subject=subject["name"],
                    correct=state["correct"],
                    total=len(tagged),
                    score=score,
                    details=json.dumps({"iq_estimate": iq_result["overall"],
                                        "domain_scores": domain_scores}),
                )

            page.clean()
            page.add(top_bar(subject["name"], show_back=True, back_fn=show_cognitive_test_menu))
            content = ft.Column([
                ft.Text("🧠 Full Cognitive Test Complete!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Score: {state['correct']} / {len(tagged)}", size=20),
                ft.Text(f"Percentage: {score}%", size=20),
                ft.Text(f"Rating: {label}", size=20, color=ft.Colors.BLUE),
                ft.Container(height=10),
                ft.Container(
                    padding=20,
                    border_radius=12,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column([
                        ft.Text(f"Estimated IQ: {iq_result['overall']}", size=24,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                        ft.Text(f"Classification: {iq_result['label']}", size=16,
                                color=ft.Colors.BLUE),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Container(height=10),
                ft.Text("⚠️ This is an estimate, not a clinically validated IQ test.",
                        size=12, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
            ])

            if domain_scores:
                content.controls.append(ft.Divider())
                content.controls.append(ft.Text("By Domain:", size=18, weight=ft.FontWeight.BOLD))
                for domain, pct in domain_scores.items():
                    color = ft.Colors.GREEN if pct >= 70 else ft.Colors.ORANGE if pct >= 50 else ft.Colors.RED
                    domain_name = next((d["name"] for d in COGNITIVE_DOMAINS if d["id"] == domain), domain)
                    content.controls.append(
                        ft.Text(f"  • {domain_name}: {pct}%", size=14, color=color)
                    )

            content.controls.append(ft.Divider())
            content.controls.append(
                ft.Button(content="Back to Cognitive Tests",
                          on_click=lambda e: show_cognitive_test_menu())
            )
            page.add(ft.Container(padding=20, content=content))
            page.update()

        page.clean()
        page.add(top_bar(subject["name"], show_back=True, back_fn=show_cognitive_test_menu))
        page.add(ft.Container(padding=20, content=ft.Column([
            back_button, ft.Divider(), progress_text, question_text,
            choices_column, feedback_text,
        ])))
        render()

    # ============================================================
    #              EQ ASSESSMENT
    # ============================================================
    def start_eq_assessment():
        questions = load_eq_assessment()
        if not questions:
            show_stub("EQ Assessment — no questions available")
            return
        fake_subject = {"id": "eq", "name": "EQ Assessment", "icon": "💗"}
        run_eq_quiz(fake_subject, questions)

    def run_eq_quiz(subject, questions):
        state = {"index": 0, "correct": 0}

        progress_text = ft.Text("", size=14, color=ft.Colors.GREY)
        question_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD)
        choices_column = ft.Column(spacing=10)
        feedback_text = ft.Text("", size=16)

        def request_exit(e):
            def close_dialog(confirmed: bool):
                confirm_dialog.open = False
                page.update()
                if confirmed:
                    show_home()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cancel this assessment?"),
                content=ft.Text("Your progress will be lost."),
                actions=[
                    ft.TextButton("Continue", on_click=lambda e: close_dialog(False)),
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
            progress_text.value = f"{subject['name']} — Question {state['index'] + 1} of {len(questions)}"
            question_text.value = q["question"]
            feedback_text.value = ""
            choices_column.controls.clear()
            for choice in q["choices"]:
                choices_column.controls.append(
                    ft.Button(content=choice, width=600,
                              on_click=lambda e, c=choice: check(c))
                )
            page.update()

        def check(choice):
            q = questions[state["index"]]
            if choice == q["answer"]:
                state["correct"] += 1
                feedback_text.value = "✅ Good emotional response!"
                feedback_text.color = ft.Colors.GREEN
            else:
                feedback_text.value = f"❌ Not the best response. {q['explanation']}"
                feedback_text.color = ft.Colors.RED
            for btn in choices_column.controls:
                btn.disabled = True
            page.update()

            async def advance():
                await asyncio.sleep(2)
                state["index"] += 1
                if state["index"] < len(questions):
                    render()
                else:
                    show_results()
            page.run_task(advance)

        def show_results():
            eq_result = calculate_eq_score(state["correct"], len(questions))

            # Save to DB
            if current_user:
                db.save_test_result(
                    user_id=current_user["id"],
                    test_type="eq",
                    subject=subject["name"],
                    correct=state["correct"],
                    total=len(questions),
                    score=eq_result["score"],
                )

            page.clean()
            page.add(top_bar(subject["name"], show_back=True, back_fn=show_home))
            content = ft.Column([
                ft.Text("💗 EQ Assessment Complete!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Score: {state['correct']} / {len(questions)}", size=20),
                ft.Text(f"Percentage: {eq_result['score']}%", size=20),
                ft.Container(height=10),
                ft.Container(
                    padding=20,
                    border_radius=12,
                    bgcolor=ft.Colors.PINK_50,
                    content=ft.Column([
                        ft.Text(eq_result["level"], size=24, weight=ft.FontWeight.BOLD,
                                color=ft.Colors.PINK),
                        ft.Text(eq_result["description"], size=15,
                                color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Divider(),
                ft.Button(content="Back to Home", on_click=lambda e: show_home()),
            ])
            page.add(ft.Container(padding=20, content=content))
            page.update()

        page.clean()
        page.add(top_bar(subject["name"], show_back=True, back_fn=show_home))
        page.add(ft.Container(padding=20, content=ft.Column([
            back_button, ft.Divider(), progress_text, question_text,
            choices_column, feedback_text,
        ])))
        render()

    # ============================================================
    #              MOCK TEST MENU
    # ============================================================
    def show_mock_test_menu():
        page.clean()
        exams = load_licensure_exams()
        content = ft.Column([
            ft.Text("📝 Mock Exam", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Choose an exam to practice with timed conditions.",
                    size=14, color=ft.Colors.GREY),
            ft.Divider(),
        ])

        if not exams:
            content.controls.append(
                ft.Text("No exams available yet.", size=16, color=ft.Colors.GREY)
            )
        else:
            for exam in exams:
                q_count = len(load_licensure_exam(exam["id"]))
                content.controls.append(
                    ft.Container(
                        padding=15,
                        margin=ft.Margin.only(bottom=8),
                        border_radius=10,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        content=ft.Row([
                            ft.Text(exam["icon"], size=24),
                            ft.Column([
                                ft.Text(exam["name"], size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(exam.get("description", ""), size=12, color=ft.Colors.GREY),
                                ft.Text(f"{q_count} questions", size=12, color=ft.Colors.BLUE),
                            ], spacing=2),
                            ft.FilledButton(
                                content=ft.Text("Configure →"),
                                on_click=lambda e, ex=exam: show_mock_config(ex),
                            ),
                        ], spacing=15),
                    )
                )

        page.add(
            top_bar("Mock Exam", show_back=True, back_fn=show_home),
            ft.Container(padding=20, content=content),
        )
        page.update()

    def show_mock_config(exam):
        page.clean()
        count_options = [5, 10, 15, 20]
        time_options = [5, 10, 15, 20, 30]  # minutes

        count_dropdown = ft.Dropdown(
            label="Number of Questions",
            options=[ft.dropdown.Option(str(c)) for c in count_options],
            value="10",
            width=200,
        )
        time_dropdown = ft.Dropdown(
            label="Time Limit (minutes)",
            options=[ft.dropdown.Option(str(t)) for t in time_options],
            value="15",
            width=200,
        )

        def start_mock(e):
            q_count = int(count_dropdown.value)
            time_limit = int(time_dropdown.value)
            questions = load_licensure_exam(exam["id"])
            if not questions:
                show_stub(f"{exam['name']} — no questions yet")
                return
            picked = pick_questions(questions, min(q_count, len(questions)))
            fake_subject = {"id": exam["id"], "name": exam["name"], "icon": exam["icon"]}
            run_mock_quiz(fake_subject, picked, time_limit * 60)

        page.add(
            top_bar(exam["name"], show_back=True, back_fn=show_mock_test_menu),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Text(f"📝 {exam['name']}", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Configure your mock exam settings.", size=14, color=ft.Colors.GREY),
                    ft.Container(height=20),
                    ft.Row([count_dropdown, time_dropdown], spacing=20),
                    ft.Container(height=20),
                    ft.FilledButton(
                        content=ft.Text("Start Timed Exam →", size=15, weight=ft.FontWeight.BOLD),
                        on_click=start_mock,
                    ),
                ], spacing=10),
            ),
        )
        page.update()

    def run_mock_quiz(subject, questions, time_limit_seconds):
        state = {"index": 0, "correct": 0, "time_remaining": time_limit_seconds}
        timer_running = {"value": True}

        timer_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        progress_text = ft.Text("", size=14, color=ft.Colors.GREY)
        question_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD)
        choices_column = ft.Column(spacing=10)
        feedback_text = ft.Text("", size=16)

        def format_time(seconds):
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins:02d}:{secs:02d}"

        def update_timer():
            timer_text.value = f"⏱️ Time remaining: {format_time(state['time_remaining'])}"
            if state['time_remaining'] <= 60:
                timer_text.color = ft.Colors.RED
            elif state['time_remaining'] <= 180:
                timer_text.color = ft.Colors.ORANGE
            else:
                timer_text.color = ft.Colors.GREEN
            page.update()

        async def timer_task():
            while state['time_remaining'] > 0 and timer_running["value"]:
                await asyncio.sleep(1)
                state['time_remaining'] -= 1
                update_timer()
            if timer_running["value"]:
                timer_running["value"] = False
                # Time's up — force finish
                for btn in choices_column.controls:
                    btn.disabled = True
                await asyncio.sleep(0.5)
                show_results()

        page.run_task(timer_task)

        def request_exit(e):
            def close_dialog(confirmed: bool):
                confirm_dialog.open = False
                page.update()
                if confirmed:
                    timer_running["value"] = False
                    show_mock_test_menu()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cancel this exam?"),
                content=ft.Text("Your progress will be lost."),
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
            if state["index"] >= len(questions):
                show_results()
                return
            q = questions[state["index"]]
            progress_text.value = f"{subject['name']} — Question {state['index'] + 1} of {len(questions)}"
            question_text.value = q["question"]
            feedback_text.value = ""
            choices_column.controls.clear()
            for choice in q["choices"]:
                choices_column.controls.append(
                    ft.Button(content=choice, width=600,
                              on_click=lambda e, c=choice: check(c))
                )
            update_timer()
            page.update()

        def check(choice):
            q = questions[state["index"]]
            if choice == q["answer"]:
                state["correct"] += 1
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
            timer_running["value"] = False
            elapsed = time_limit_seconds - state["time_remaining"]
            score = calculate_score(state["correct"], len(questions))
            label = grade_label(score)

            # Save to DB
            if current_user:
                db.save_test_result(
                    user_id=current_user["id"],
                    test_type="mock_exam",
                    subject=subject["name"],
                    correct=state["correct"],
                    total=len(questions),
                    score=score,
                    duration_seconds=elapsed,
                )

            page.clean()
            page.add(top_bar(subject["name"], show_back=True, back_fn=show_mock_test_menu))
            content = ft.Column([
                ft.Text("📝 Exam Complete!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Score: {state['correct']} / {len(questions)}", size=20),
                ft.Text(f"Percentage: {score}%", size=20),
                ft.Text(f"Rating: {label}", size=20, color=ft.Colors.BLUE),
                ft.Text(f"Time: {format_time(elapsed)} / {format_time(time_limit_seconds)}", size=16),
                ft.Divider(),
                ft.Button(content="Back to Mock Exams",
                          on_click=lambda e: show_mock_test_menu()),
            ])
            page.add(ft.Container(padding=20, content=content))
            page.update()

        page.clean()
        page.add(top_bar(subject["name"], show_back=True, back_fn=show_mock_test_menu))
        page.add(ft.Container(padding=20, content=ft.Column([
            ft.Row([back_button, timer_text, ft.Container(expand=True)], spacing=10),
            ft.Divider(),
            progress_text,
            question_text,
            choices_column,
            feedback_text,
        ])))
        render()

    # ============================================================
    #              LEARNING MODE
    # ============================================================
    LESSON_SUBJECT_MAP = {
        "mathematics": "Mathematics",
        "sciences": "Sciences",
        "english": "English / Language Arts",
    }

    def show_learning_mode():
        page.clean()
        content = ft.Column([
            ft.Text("📚 Learning Mode", size=28, weight=ft.FontWeight.BOLD),
        ])

        if not current_user:
            content.controls.extend([
                ft.Text("Login to get personalized recommendations based on your performance.",
                        size=14, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.FilledButton(content=ft.Text("Login →"),
                                  on_click=lambda e: show_login()),
                ft.Divider(),
                ft.Text("Browse Available Lessons:", size=18, weight=ft.FontWeight.BOLD),
            ])
        else:
            plan = recommender.get_study_plan(current_user["id"])
            if plan:
                content.controls.append(
                    ft.Text("Your Personalized Study Plan:", size=16, weight=ft.FontWeight.BOLD)
                )
                for rec in plan:
                    priority_color = (
                        ft.Colors.RED if rec["priority"] == "High"
                        else ft.Colors.ORANGE if rec["priority"] == "Medium"
                        else ft.Colors.GREEN
                    )
                    content.controls.append(
                        ft.Container(
                            padding=12,
                            margin=ft.Margin.only(bottom=6),
                            border_radius=8,
                            bgcolor=priority_color + "_50" if hasattr(ft.Colors, priority_color + "_50") else ft.Colors.GREY_50,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(rec["subject"], size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{rec['priority']}", size=12, color=priority_color,
                                            weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Text(rec["reason"], size=12, color=ft.Colors.GREY),
                                ft.Text(f"Action: {rec['action']}", size=12, italic=True),
                            ], spacing=2),
                        )
                    )
            else:
                content.controls.append(
                    ft.Text("No recommendations yet. Take some tests first!",
                            size=14, color=ft.Colors.GREY)
                )

            content.controls.append(ft.Divider())
            content.controls.append(
                ft.Text("Browse Available Lessons:", size=18, weight=ft.FontWeight.BOLD)
            )

        # Show available lessons
        lessons = recommender.get_available_lessons()
        if lessons:
            for lesson in lessons:
                content.controls.append(
                    ft.Container(
                        padding=12,
                        margin=ft.Margin.only(bottom=6),
                        border_radius=8,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        content=ft.Row([
                            ft.Text("📖", size=20),
                            ft.Column([
                                ft.Text(lesson["name"], size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(lesson["description"], size=12, color=ft.Colors.GREY),
                            ], spacing=2),
                            ft.FilledButton(
                                content=ft.Text("Read →"),
                                on_click=lambda e, lid=lesson["id"]: show_lesson(lid),
                            ),
                        ], spacing=10),
                    )
                )
        else:
            content.controls.append(
                ft.Text("No lessons available yet.", size=14, color=ft.Colors.GREY)
            )

        content.controls.append(ft.Divider())
        content.controls.append(
            ft.Text("📝 Daily Homework Quiz", size=18, weight=ft.FontWeight.BOLD)
        )
        content.controls.append(
            ft.Text("Take a quick 5-question quiz to practice.", size=13, color=ft.Colors.GREY)
        )
        for subj_id, subj_name in LESSON_SUBJECT_MAP.items():
            content.controls.append(
                ft.OutlinedButton(
                    content=ft.Text(f"{subj_name} Homework Quiz"),
                    on_click=lambda e, sid=subj_id: start_practice_quiz(sid, subj_name),
                )
            )

        page.add(
            top_bar("Learning Mode", show_back=True, back_fn=show_home),
            ft.Container(padding=20, content=content),
        )
        page.update()

    def show_lesson(subject_id):
        lesson = recommender.get_lesson(subject_id)
        if not lesson:
            show_stub(f"Lesson — {subject_id} not found")
            return

        content = ft.Column([
            ft.Text(lesson["title"], size=26, weight=ft.FontWeight.BOLD),
            ft.Text(lesson.get("description", ""), size=14, color=ft.Colors.GREY),
            ft.Divider(),
        ])

        for section in lesson.get("sections", []):
            content.controls.extend([
                ft.Text(section["heading"], size=18, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE),
                ft.Text(section["content"], size=14),
                ft.Container(height=8),
            ])

        # Practice quiz button
        if lesson.get("practice_questions"):
            content.controls.extend([
                ft.Divider(),
                ft.Text("Test Your Knowledge", size=18, weight=ft.FontWeight.BOLD),
                ft.FilledButton(
                    content=ft.Text(f"📝 Take Practice Quiz ({len(lesson['practice_questions'])} questions)"),
                    on_click=lambda e, sid=subject_id: start_lesson_quiz(sid),
                ),
            ])

        page.add(
            top_bar("Lesson", show_back=True, back_fn=show_learning_mode),
            ft.Container(padding=20, content=content),
        )
        page.update()

    def start_lesson_quiz(subject_id):
        lesson = recommender.get_lesson(subject_id)
        questions = lesson.get("practice_questions", [])
        if not questions:
            show_stub("No practice questions available")
            return
        lesson_title = lesson.get("title", subject_id)
        fake_subject = {"id": subject_id, "name": f"{lesson_title} — Practice", "icon": "📝"}
        run_quiz(fake_subject, questions, is_pretest=False)

    def start_practice_quiz(subject_id, subject_name):
        questions = recommender.get_homework_quiz(subject_id, count=5)
        if not questions:
            show_stub(f"{subject_name} — no homework questions available")
            return
        fake_subject = {"id": subject_id, "name": f"{subject_name} Homework", "icon": "📝"}
        run_quiz(fake_subject, questions, is_pretest=False)

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

        name = current_user["name"] if current_user else "Guest"
        initial = name[0].upper() if name else "G"
        email = current_user.get("email", "N/A") if current_user else "N/A"

        page.add(
            top_bar("Profile", show_back=True, back_fn=show_home),
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(initial, size=36),
                            radius=48,
                            bgcolor=ft.Colors.BLUE_400,
                        ),
                        ft.Column([
                            ft.Text(name, size=26, weight=ft.FontWeight.BOLD),
                            ft.Text("Student", size=14, color=ft.Colors.GREY),
                        ], spacing=2),
                    ], spacing=20),
                    ft.Divider(),
                    ft.Text(f"Email: {email}", size=14),
                    ft.Text(f"Account ID: {current_user['id']}" if current_user else "Guest mode — no account.", size=14, color=ft.Colors.GREY),
                ]),
            ),
        )
        page.update()

    # ============================================================
    #                     STATISTICS PAGE
    # ============================================================
    def show_statistics():
        page.clean()

        if not current_user:
            page.add(
                top_bar("Statistics", show_back=True, back_fn=show_home),
                ft.Container(
                    padding=30,
                    content=ft.Column([
                        ft.Text("📊", size=64),
                        ft.Text("Your Stats", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Login to see your test history and trends.",
                                size=14, color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=10),
                        ft.FilledButton(
                            content=ft.Text("Login →"),
                            on_click=lambda e: show_login(),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            )
            page.update()
            return

        stats = db.get_user_stats(current_user["id"])

        content = ft.Column([
            ft.Text("📊 Your Stats", size=26, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                ft.Container(
                    padding=15,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column([
                        ft.Text(str(stats["total_tests"]), size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Total Tests", size=12, color=ft.Colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Container(
                    padding=15,
                    border_radius=10,
                    bgcolor=ft.Colors.GREEN_50,
                    content=ft.Column([
                        ft.Text(f"{stats['average_score']}%", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Average Score", size=12, color=ft.Colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Container(
                    padding=15,
                    border_radius=10,
                    bgcolor=ft.Colors.ORANGE_50,
                    content=ft.Column([
                        ft.Text(f"{stats['best_score']}%", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Best Score", size=12, color=ft.Colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            ], spacing=15),
        ])

        if stats["by_subject"]:
            content.controls.append(ft.Divider())
            content.controls.append(ft.Text("By Subject:", size=18, weight=ft.FontWeight.BOLD))
            for s in stats["by_subject"]:
                pct = s["avg_score"]
                color = (
                    ft.Colors.GREEN if pct >= 70
                    else ft.Colors.ORANGE if pct >= 50
                    else ft.Colors.RED
                )
                content.controls.append(
                    ft.Row([
                        ft.Text(f"• {s['subject']}", size=14),
                        ft.Text(f"{pct}% ({s['test_count']} tests)", size=14, color=color, expand=True,
                                text_align=ft.TextAlign.END),
                    ])
                )

        if stats["by_type"]:
            content.controls.append(ft.Divider())
            content.controls.append(ft.Text("By Test Type:", size=18, weight=ft.FontWeight.BOLD))
            for t in stats["by_type"]:
                content.controls.append(
                    ft.Text(f"  • {t['test_type']}: {t['avg_score']}% avg ({t['test_count']} tests)",
                            size=14)
                )

        # Recent test history
        recent_results = db.get_user_test_results(current_user["id"], limit=10)
        if recent_results:
            content.controls.append(ft.Divider())
            content.controls.append(ft.Text("Recent Tests:", size=18, weight=ft.FontWeight.BOLD))
            for r in recent_results:
                color = ft.Colors.GREEN if r["score"] >= 70 else ft.Colors.ORANGE if r["score"] >= 50 else ft.Colors.RED
                content.controls.append(
                    ft.Row([
                        ft.Text(f"• {r['test_type']} — {r.get('subject', 'N/A')}", size=13),
                        ft.Text(f"{r['score']}%", size=13, color=color, weight=ft.FontWeight.BOLD,
                                expand=True, text_align=ft.TextAlign.END),
                    ])
                )

        # CSV export
        content.controls.append(ft.Divider())
        def export_csv(e):
            filepath = db.export_results_to_csv(current_user["id"])
            if filepath:
                export_status.value = f"✅ Exported to {filepath}"
                export_status.color = ft.Colors.GREEN
            else:
                export_status.value = "No results to export."
                export_status.color = ft.Colors.GREY
            page.update()

        export_status = ft.Text("", size=13)
        content.controls.extend([
            ft.FilledButton(content=ft.Text("📥 Export Results to CSV"), on_click=export_csv),
            export_status,
        ])

        page.add(
            top_bar("Statistics", show_back=True, back_fn=show_home),
            ft.Container(padding=20, content=content),
        )
        page.update()

    # ============================================================
    #                   RECOMMENDATIONS PAGE
    # ============================================================
    def show_recommendations():
        page.clean()

        if not current_user:
            page.add(
                top_bar("Recommendations", show_back=True, back_fn=show_home),
                ft.Container(
                    padding=30,
                    content=ft.Column([
                        ft.Text("💡", size=64),
                        ft.Text("Personalized Suggestions", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Login to see study recommendations based on your performance.",
                                size=14, color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=10),
                        ft.FilledButton(
                            content=ft.Text("Login →"),
                            on_click=lambda e: show_login(),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            )
            page.update()
            return

        weak = db.get_weak_areas(current_user["id"])

        content = ft.Column([
            ft.Text("💡 Recommendations", size=26, weight=ft.FontWeight.BOLD),
        ])

        if not weak:
            content.controls.extend([
                ft.Text("🎉 Great job!", size=20, color=ft.Colors.GREEN),
                ft.Text("You're performing well across all subjects. "
                        "Try taking more challenging tests to keep improving.",
                        size=14, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
            ])
        else:
            content.controls.append(
                ft.Text("Based on your recent tests, focus on these areas:",
                        size=14, color=ft.Colors.GREY)
            )
            for w in weak:
                content.controls.append(
                    ft.Container(
                        padding=15,
                        margin=ft.Margin.only(top=8),
                        border_radius=10,
                        bgcolor=ft.Colors.RED_50,
                        content=ft.Row([
                            ft.Text("⚠️", size=20),
                            ft.Column([
                                ft.Text(w["subject"], size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Average: {w['avg_score']}% ({w['test_count']} tests)",
                                        size=12, color=ft.Colors.GREY),
                            ], spacing=2),
                        ], spacing=10),
                    )
                )

            content.controls.extend([
                ft.Container(height=10),
                ft.Text("Suggested actions:", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("• Review lessons for your weakest subjects", size=13),
                ft.Text("• Take practice quizzes to reinforce learning", size=13),
                ft.Text("• Retake tests after studying to track improvement", size=13),
            ])

        page.add(
            top_bar("Recommendations", show_back=True, back_fn=show_home),
            ft.Container(padding=20, content=content),
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
    def run_quiz(subject, questions, is_pretest=False, is_onboarding=False):
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
                    if is_onboarding:
                        show_signup()
                    elif is_pretest:
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

            # Save to database if user is logged in
            if current_user:
                details = json.dumps({
                    "by_type": state["by_type"],
                    "by_subject": state["by_subject"] if is_pretest else {},
                })
                db.save_test_result(
                    user_id=current_user["id"],
                    test_type="onboarding" if is_onboarding else ("pretest" if is_pretest else "subject"),
                    subject=subject["name"],
                    correct=state["correct"],
                    total=len(questions),
                    score=score,
                    details=details,
                )

            page.clean()
            back_target = show_signup if is_onboarding else show_home
            page.add(top_bar(subject["name"], show_back=True, back_fn=back_target))

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

            if is_onboarding:
                content.controls.append(
                    ft.Text("Great job! Now create an account to save your progress.",
                            size=14, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER)
                )
                content.controls.append(
                    ft.FilledButton(
                        content=ft.Text("Create Account →"),
                        on_click=lambda e: show_signup(),
                    )
                )
                content.controls.append(
                    ft.TextButton(
                        content=ft.Text("Skip — Go to Home →"),
                        on_click=lambda e: show_home(),
                    )
                )
            else:
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
    # Check if user has an account; if not, show onboarding
    show_onboarding()

ft.run(main)
