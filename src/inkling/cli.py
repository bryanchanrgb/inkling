"""Interactive CLI interface for the learning application."""

from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.text import Text

from .models import Answer, Question, Topic
from .quiz_service import QuizService
from .storage import Storage
from .topic_service import TopicService


class CLI:
    """Interactive command-line interface."""
    
    def __init__(self):
        """Initialize CLI."""
        self.console = Console()
        self.topic_service = TopicService()
        self.quiz_service = QuizService()
        self.storage = Storage()
    
    def run(self):
        """Run the main CLI loop."""
        self.console.print(Panel.fit(
            "[bold blue]Inkling[/bold blue] - Learning Application with Knowledge Graphs",
            border_style="blue"
        ))
        
        while True:
            self._show_main_menu()
            choice = Prompt.ask("\n[bold]Select an option[/bold]", choices=["1", "2", "3", "4", "5", "6"], default="6")
            
            try:
                if choice == "1":
                    self._create_topic()
                elif choice == "2":
                    self._start_quiz()
                elif choice == "3":
                    self._view_topics()
                elif choice == "4":
                    self._view_quiz_history()
                elif choice == "5":
                    self._generate_additional_questions()
                elif choice == "6":
                    self.console.print("\n[green]Goodbye![/green]")
                    self.topic_service.close()
                    break
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Operation cancelled.[/yellow]")
            except Exception as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]")
    
    def _show_main_menu(self):
        """Display the main menu."""
        menu = Table.grid(padding=1)
        menu.add_column(style="cyan", justify="right")
        menu.add_column(style="bold")
        
        menu.add_row("1", "Create new topic")
        menu.add_row("2", "Start quiz for topic")
        menu.add_row("3", "View topics")
        menu.add_row("4", "View quiz history")
        menu.add_row("5", "Generate additional questions")
        menu.add_row("6", "Exit")
        
        self.console.print("\n[bold]Main Menu[/bold]")
        self.console.print(menu)
    
    def _create_topic(self):
        """Create a new topic."""
        self.console.print("\n[bold cyan]Create New Topic[/bold cyan]")
        topic_name = Prompt.ask("Enter topic name")
        
        if not topic_name.strip():
            self.console.print("[red]Topic name cannot be empty.[/red]")
            return
        
        self.console.print(f"\n[yellow]Creating topic '{topic_name}'...[/yellow]")
        self.console.print("[dim]This may take a moment as we generate the knowledge graph and questions.[/dim]")
        
        with self.console.status("[bold green]Generating knowledge graph and questions..."):
            topic, questions = self.topic_service.create_topic(topic_name)
        
        self.console.print(f"\n[green]✓ Topic created successfully![/green]")
        self.console.print(f"  Topic: [bold]{topic.name}[/bold]")
        self.console.print(f"  Questions generated: [bold]{len(questions)}[/bold]")
        
        # Show subtopics
        subtopics = self.topic_service.get_subtopics(topic_name)
        if subtopics:
            self.console.print(f"\n[bold]Subtopics:[/bold]")
            for subtopic in subtopics:
                self.console.print(f"  • {subtopic['name']}")
    
    def _start_quiz(self):
        """Start a quiz for a topic."""
        topics = self.topic_service.list_topics()
        
        if not topics:
            self.console.print("\n[red]No topics found. Please create a topic first.[/red]")
            return
        
        self.console.print("\n[bold cyan]Start Quiz[/bold cyan]")
        self._display_topics_table(topics)
        
        topic_choice = IntPrompt.ask(
            "\nSelect a topic (enter number)",
            choices=[str(i + 1) for i in range(len(topics))],
            default="1"
        )
        
        selected_topic = topics[int(topic_choice) - 1]
        
        self.console.print(f"\n[bold]Starting quiz for: {selected_topic.name}[/bold]")
        
        try:
            questions = self.quiz_service.start_quiz(selected_topic.id)
        except ValueError as e:
            self.console.print(f"[red]{str(e)}[/red]")
            return
        
        if not questions:
            self.console.print("[red]No questions available for this topic.[/red]")
            return
        
        self.console.print(f"[dim]You will be asked {len(questions)} questions.[/dim]\n")
        
        answers: List[Answer] = []
        
        for i, question in enumerate(questions, 1):
            self.console.print(Panel(
                f"[bold]{question.question_text}[/bold]",
                title=f"Question {i}/{len(questions)}",
                border_style="blue"
            ))
            
            if question.subtopic:
                self.console.print(f"[dim]Subtopic: {question.subtopic}[/dim]")
            if question.difficulty:
                self.console.print(f"[dim]Difficulty: {question.difficulty}[/dim]")
            
            user_answer = Prompt.ask("\n[bold]Your answer[/bold]")
            
            if not user_answer.strip():
                self.console.print("[yellow]Empty answer submitted.[/yellow]")
                user_answer = "(no answer provided)"
            
            self.console.print("[dim]Grading your answer...[/dim]")
            
            with self.console.status("[bold green]Grading..."):
                answer = self.quiz_service.grade_answer(question, user_answer)
            
            answers.append(answer)
            
            # Display feedback
            if answer.is_correct:
                self.console.print(f"\n[green]✓ Correct![/green]")
            else:
                self.console.print(f"\n[red]✗ Incorrect[/red]")
            
            if answer.feedback:
                self.console.print(Panel(
                    answer.feedback,
                    title="Feedback",
                    border_style="yellow" if answer.is_correct else "red"
                ))
            
            if answer.understanding_score is not None:
                self.console.print(f"[dim]Understanding Score: {answer.understanding_score}/5[/dim]")
            
            self.console.print()  # Blank line between questions
        
        # Show results
        results = self.quiz_service.get_quiz_results(answers)
        self._display_quiz_results(results)
    
    def _view_topics(self):
        """View all topics."""
        topics = self.topic_service.list_topics()
        
        if not topics:
            self.console.print("\n[red]No topics found.[/red]")
            return
        
        self.console.print("\n[bold cyan]Topics[/bold cyan]")
        self._display_topics_table(topics)
    
    def _display_topics_table(self, topics: List[Topic]):
        """Display topics in a table."""
        table = Table(title="Topics", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold")
        table.add_column("Description", style="dim")
        table.add_column("Created", style="dim")
        
        for i, topic in enumerate(topics, 1):
            created_str = topic.created_at.strftime("%Y-%m-%d") if topic.created_at else "N/A"
            desc = topic.description or ""
            if len(desc) > 50:
                desc = desc[:47] + "..."
            table.add_row(
                str(i),
                topic.name,
                desc,
                created_str
            )
        
        self.console.print(table)
    
    def _view_quiz_history(self):
        """View quiz history."""
        topics = self.topic_service.list_topics()
        
        if not topics:
            self.console.print("\n[red]No topics found.[/red]")
            return
        
        self.console.print("\n[bold cyan]Quiz History[/bold cyan]")
        self._display_topics_table(topics)
        
        topic_choice = Prompt.ask(
            "\nSelect a topic to view history (or press Enter for all topics)",
            default=""
        )
        
        topic_id = None
        if topic_choice:
            try:
                selected_topic = topics[int(topic_choice) - 1]
                topic_id = selected_topic.id
            except (ValueError, IndexError):
                self.console.print("[red]Invalid topic selection.[/red]")
                return
        
        history = self.quiz_service.get_quiz_history(topic_id, limit=20)
        
        if not history:
            self.console.print("\n[yellow]No quiz history found.[/yellow]")
            return
        
        table = Table(title="Quiz History", show_header=True, header_style="bold cyan")
        table.add_column("Question", style="bold", width=40)
        table.add_column("Your Answer", width=30)
        table.add_column("Correct", style="bold", width=8)
        table.add_column("Score", width=8)
        table.add_column("Date", style="dim", width=12)
        
        for record in history:
            is_correct_text = Text("✓", style="green") if record['is_correct'] else Text("✗", style="red")
            score_text = f"{record['understanding_score']}/5" if record['understanding_score'] else "N/A"
            
            question = record['question_text']
            if len(question) > 37:
                question = question[:34] + "..."
            
            user_ans = record['user_answer']
            if len(user_ans) > 27:
                user_ans = user_ans[:24] + "..."
            
            timestamp = record['timestamp']
            if isinstance(timestamp, str):
                date_str = timestamp[:10] if len(timestamp) >= 10 else timestamp
            else:
                date_str = str(timestamp)[:10]
            
            table.add_row(
                question,
                user_ans,
                is_correct_text,
                score_text,
                date_str
            )
        
        self.console.print(table)
    
    def _display_quiz_results(self, results: dict):
        """Display quiz results."""
        self.console.print("\n[bold cyan]Quiz Results[/bold cyan]")
        
        table = Table(show_header=False, box=None)
        table.add_column(style="bold")
        table.add_column()
        
        table.add_row("Total Questions:", str(results['total_questions']))
        table.add_row("Correct Answers:", f"[green]{results['correct_answers']}[/green]")
        table.add_row("Incorrect Answers:", f"[red]{results['incorrect_answers']}[/red]")
        table.add_row("Score:", f"[bold]{results['score']:.1f}%[/bold]")
        table.add_row("Average Understanding:", f"{results['average_understanding']:.1f}/5")
        
        self.console.print(table)
        
        # Show performance message
        score = results['score']
        if score >= 80:
            self.console.print("\n[green]Excellent work![/green]")
        elif score >= 60:
            self.console.print("\n[yellow]Good job! Keep practicing.[/yellow]")
        else:
            self.console.print("\n[red]Keep studying! You'll improve with practice.[/red]")
    
    def _generate_additional_questions(self):
        """Generate additional questions for a topic."""
        topics = self.topic_service.list_topics()
        
        if not topics:
            self.console.print("\n[red]No topics found. Please create a topic first.[/red]")
            return
        
        self.console.print("\n[bold cyan]Generate Additional Questions[/bold cyan]")
        self._display_topics_table(topics)
        
        topic_choice = IntPrompt.ask(
            "\nSelect a topic (enter number)",
            choices=[str(i + 1) for i in range(len(topics))],
            default="1"
        )
        
        selected_topic = topics[int(topic_choice) - 1]
        
        self.console.print(f"\n[bold]Generating additional questions for: {selected_topic.name}[/bold]")
        self.console.print("[dim]Analyzing learning gaps and existing questions...[/dim]")
        
        try:
            with self.console.status("[bold green]Generating questions..."):
                question_data = self.quiz_service.generate_additional_questions(selected_topic.id)
            
            if not question_data:
                self.console.print("[yellow]No new questions were generated.[/yellow]")
                return
            
            # Save questions to database
            questions = []
            for q_data in question_data:
                question = Question(
                    topic_id=selected_topic.id,
                    question_text=q_data.get('question_text', ''),
                    correct_answer=q_data.get('correct_answer', ''),
                    subtopic=q_data.get('subtopic'),
                    difficulty=q_data.get('difficulty')
                )
                question_id = self.storage.save_question(question)
                question.id = question_id
                questions.append(question)
            
            self.console.print(f"\n[green]✓ Generated {len(questions)} new questions![/green]")
        
        except ValueError as e:
            self.console.print(f"[red]{str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error generating questions: {str(e)}[/red]")

