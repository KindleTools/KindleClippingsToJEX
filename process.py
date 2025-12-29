from csv import DictReader
from datetime import datetime
from joplin import notebook, note, tag, tag_note, jex
from kindle import get_highlights

LOCATION = (0, 0, 0)
CREATOR = "SYSTEM"

AUTHORS = {}
BOOKS = {}
TAGS = {}


def __database_nb(key, obj, fn, args={}):
    if key in obj:
        return obj[key]
    else:
        ide = fn(**args)
        obj[key] = ide
        return ide


def __date(data, pattern=None):
    try:
        if isinstance(data, datetime):
            res = data
        else:
            res = datetime.strptime(data, pattern)
    except ValueError:
        if len(data) > 10:
            res = datetime.strptime(data, '%d/%m/%Y %H:%M')
        else:
            res = datetime.strptime(data, '%d/%m/%Y')
    return res.isoformat('T', 'milliseconds')


def __title(title, subtitle):
    ref = '[{}] '.format('{:04d}'.format(int(subtitle)) if subtitle.isnumeric() else subtitle) \
        if len(subtitle) and len(subtitle) < 7 else ''
    return '{}{}'.format(ref, title)


def __metadata(text, row):
    values = ['date', 'author', 'book', 'page', 'tags']
    return text + "\n\n\n-----\n" + "\n".join(['- {}: {}'.format(value, row[value]) for value in values if row[value]]) + "\n-----\n"


def ini_process(nb="IMPORT"):
    return notebook(nb)


def end_process(outfile="joplin"):
    return jex(outfile)


def csv_process(infile, location=LOCATION, creator=CREATOR, parent=None, metadata=True, outfile=None,
                dateformat='%d/%m/%Y %H:%M:%S', encoding='utf-8-sig', delimiter=','):
    with open(infile, encoding=encoding) as csv_file:
        reader = DictReader(csv_file, delimiter=delimiter)

        nb = ini_process() if parent is None else parent

        for row in reader:
            jex_process(nb, row, location, creator, metadata, dateformat)

    return jex(outfile) if outfile else None


def kindle_process(infile, location=LOCATION, creator=CREATOR, parent=None, metadata=True, outfile=None):
    nb = ini_process() if parent is None else parent

    for row in get_highlights(infile):
        jex_process(nb, row, location, creator, metadata)

    return jex(outfile) if outfile else None


def jex_process(nb, row, location, creator, metadata, dateformat=None):
    date = __date(row['date'], dateformat)
    title = __title(row['title'], row['page'])
    body = __metadata(row['text'], row) if metadata else row['text']

    author = __database_nb(row['author'], AUTHORS, notebook,
                            {'title': row['author'].upper(), 'parent': nb, 'date': date}
                            )
    __database_nb(author, BOOKS, dict)
    book = __database_nb(row['book'], BOOKS[author], notebook,
                            {'title': row['book'], 'parent': author, 'date': date}
                            )

    quote = note(
        title, body, book, date, author=creator,
        latitude=location[0], longitude=location[1], altitude=location[2]
    )

    if len(row['tags']):
        for key in row['tags'].split(','):
            keyword = __database_nb(key.strip(), TAGS, tag, {'title': key.strip(), 'date': date})
            tag_note(keyword, quote)
