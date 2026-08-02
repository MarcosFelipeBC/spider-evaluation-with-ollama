def create_prompt(schema: str, question: str) -> str:
    return f"""
{schema}

Gere uma consulta SQL válida para SQLite que responda à pergunta considerando apenas as tabelas fornecidas acima.
Retorne somente uma consulta SQL, sem explicações e sem Markdown.

Pergunta: {question}
SQL:
""".strip()
