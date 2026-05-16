from typing import Any

from bs4 import BeautifulSoup as bs
from django.http import HttpResponse
from rich.console import Console
from rich.syntax import Syntax


def beautify_response(response: HttpResponse | Any):
    soup = bs(response.content, "html.parser")
    html_formatado = soup.prettify()
    syntax = Syntax(
        html_formatado,
        "html",
        theme="monokai",
        line_numbers=True,
        word_wrap=True,
    )
    console = Console(force_terminal=True)
    console.print(syntax)
