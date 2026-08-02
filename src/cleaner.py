import re

def clean_sql(raw: str) -> str:
    # Remove espaços em branco e quebras de linha do início e do fim da resposta.
    value = raw.strip()

    # Remove a marcação de abertura de um bloco Markdown, como ```sql ou ```.
    # O parâmetro re.I faz com que "sql" seja reconhecido independentemente
    # de estar escrito com letras maiúsculas ou minúsculas.
    value = re.sub(r"^```(?:sql)?\s*", "", value, flags=re.I)

    # Remove a marcação de fechamento ``` localizada no final da resposta.
    value = re.sub(r"\s*```$", "", value)

    # Remove novamente eventuais espaços ou quebras de linha restantes.
    return value.strip()