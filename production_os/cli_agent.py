"""
Interactive Terminal CLI for Production Manager OS
Provides an interactive command prompt and Rich UI in the terminal.

Branding: Saurabh Patil - Production Manager
"""

import sys
import os
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from production_os.core.production_engine import ProductionEngine
from production_os.core.ai_agent import ProductionAIAgent

def run_cli():
    engine = ProductionEngine()
    ai = ProductionAIAgent(engine)

    print("=" * 70)
    print("🎬  SAURABH PATIL • PRODUCTION MANAGER OS (CLI)")
    print(f"📅  Active Tracking Date: {datetime.now().strftime('%A, %d %B %Y')}")
    print(f"📊  Master Spreadsheet: {engine.excel_path}")
    print("=" * 70)
    print("\n💡 Type any natural production command, e.g.:")
    print("   • 'Check out Sony FX6 to Rohit for Tata Shoot until Friday'")
    print("   • 'Check in DISP-20260812-001 clean condition'")
    print("   • 'Log DPR for Tata Shoot: wrap 8 PM, 6 scenes done, 350GB'")
    print("   • 'Add expense: 2500 for generator fuel paid by Assistant'")
    print("   • 'Show available gear'")
    print("   • 'Clear all data'")
    print("   • 'Summary' or 'Status'")
    print("   • Type 'exit' or 'quit' to close.\n")

    while True:
        try:
            prompt = input("🎬 [Saurabh Patil Desk] > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "quit", "q"]:
                print("\n👋 Exiting Production Manager. Master Excel is up to date!")
                break

            res = ai.process_command(prompt)
            print("\n" + res.get("message", "Processed successfully.") + "\n" + "-" * 70)

        except KeyboardInterrupt:
            print("\n👋 Session closed.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    run_cli()
