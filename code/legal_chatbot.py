import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from search_engine import SearchEngine, SearchMode
from llm_client import LLMClient
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from config import Config

console = Console()

class LegalChatbot:
    def __init__(self):
        # Load .env from parent directory
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)
        
        self.engine = SearchEngine()
        self.llm = LLMClient()
        self.full_text_dir = Path(Config.FULL_TEXTS_DIR)

    def process_query(self, query: str):
        with console.status("[bold green]Searching precedents..."):
            results = self.engine.search(query, limit=5, mode=SearchMode.HYBRID)
        
        if not results:
            console.print("[bold red]No relevant legal precedents found in the database.[/bold red]")
            return

        # Hydrate context
        context_docs = []
        for res in results:
            doc = {'title': res['title'], 'text': ''}
            file_path = self.full_text_dir / f"{res['case_id']}.txt"
            if file_path.exists():
                doc['text'] = file_path.read_text(encoding='utf-8', errors='ignore')[:3500]
            context_docs.append(doc)

        with console.status("[bold yellow]Synthesizing legal advice..."):
            answer = self.llm.generate_answer(query, context_docs)
            
        if answer:
            console.print("\n" + "─"* console.width)
            console.print(Panel(
                Markdown(answer), 
                title="⚖️ Legal Assistant Recommendation", 
                subtitle=f"Based on {len(results)} precedents",
                border_style="cyan"
            ))
            console.print("─"* console.width + "\n")
        else:
            console.print("[bold red]Consultation failed. Try reformatting your query.[/bold red]")

    def run(self):
        console.print(Panel.fit(
            "[bold white]Welcome to the AI Legal Research Assistant[/bold white]\n"
            "[dim]Powered by Hybrid Retrieval (Sparse + Dense + Graph)[/dim]",
            border_style="bold blue"
        ))
        
        while True:
            query = Prompt.ask("\n[bold yellow]How can I help you today?[/bold yellow] (or type 'exit')")
            
            if query.lower() in ["exit", "quit", "q"]:
                console.print("[bold blue]Closing legal advisor session. Goodbye![/bold blue]")
                break
                
            if not query.strip():
                continue
                
            self.process_query(query)

if __name__ == "__main__":
    bot = LegalChatbot()
    
    # Handle direct query from command line if provided
    if len(sys.argv) > 1:
        bot.process_query(" ".join(sys.argv[1:]))
    else:
        bot.run()
