#!/usr/bin/env python3
"""
CLI for Retail Analytics Copilot - exact assignment contract.
"""

import json
import click
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.graph_hybrid_new import create_agent
from agent.dspy_signatures import configure_dspy_modules


@click.command()
@click.option('--batch', required=True, help='JSONL file with questions')
@click.option('--out', required=True, help='Output JSONL file')
def main(batch: str, out: str):
    """
    Run retail analytics agent on batch questions.
    
    Exact CLI contract as specified in assignment.
    """
    
    # Paths
    db_path = "data/northwind.sqlite"
    docs_path = "docs/"
    
    # Verify files exist
    if not os.path.exists(db_path):
        click.echo(f"Error: Database not found at {db_path}")
        sys.exit(1)
        
    if not os.path.exists(docs_path):
        click.echo(f"Error: Docs directory not found at {docs_path}")
        sys.exit(1)
        
    if not os.path.exists(batch):
        click.echo(f"Error: Batch file not found at {batch}")
        sys.exit(1)
    
    # Configure DSPy for local Ollama
    try:
        configure_dspy_modules()
        click.echo("✓ Configured DSPy with Ollama")
    except Exception as e:
        click.echo(f"Warning: DSPy configuration failed: {e}")
        click.echo("Continuing with fallback logic...")
    
    # Create agent
    try:
        agent = create_agent(db_path, docs_path)
        click.echo("✓ Agent initialized")
    except Exception as e:
        click.echo(f"Error: Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Process questions
    results = []
    
    with open(batch, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                question_data = json.loads(line.strip())
                click.echo(f"Processing question {line_num}: {question_data.get('id', 'unknown')}")
                
                # Run agent
                result = agent.run(question_data)
                results.append(result)
                
                click.echo(f"  Answer: {result.get('final_answer')}")
                click.echo(f"  Confidence: {result.get('confidence', 0):.2f}")
                
            except json.JSONDecodeError:
                click.echo(f"Error: Invalid JSON on line {line_num}")
                continue
            except Exception as e:
                click.echo(f"Error processing question {line_num}: {e}")
                # Still output a result
                results.append({
                    "id": question_data.get("id", f"line_{line_num}") if 'question_data' in locals() else f"line_{line_num}",
                    "final_answer": 0,
                    "sql": "",
                    "confidence": 0.0,
                    "explanation": f"Processing failed: {str(e)}",
                    "citations": []
                })
    
    # Write outputs
    try:
        with open(out, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, default=str) + '\n')
        
        click.echo(f"✓ Results written to {out}")
        click.echo(f"Processed {len(results)} questions")
        
    except Exception as e:
        click.echo(f"Error writing output: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
