from yattag import Doc, indent
from pathlib2 import PurePath



def create_html_index(target_dir, parent_dir, pages):
    doc, tag, text = Doc().tagtext()
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
        with tag('style', type="text/css"):
            text('table { border-collapse: collapse } ')
            text('table, th, td { border: 1px solid black; padding: 4px } ')
        with tag('body'):
            with tag('h1'):
                text('Directory Listing for /' + target_dir)
            doc.stag('hr')
            with tag('table'):
                with tag('tr'):
                    with tag('td'):
                        with tag('a', href = '/' + parent_dir):
                            text('Parent Directory')
                for page in pages:
                    page_path = PurePath(page)
                    with tag('tr'):
                        with tag('td'):
                            with tag('a', href = '/' + page):
                                text(page_path.name)

    return indent(doc.getvalue(), newline = '\r\n')
