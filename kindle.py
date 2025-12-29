# ref: https://gitlab.com/seawind/kindle-highlights-in-joplin
import re
import dateparser

path_highlights = "files/My Clippings.txt"
separator = "=========="

highl_kws = 'subrayado|Subrayado'
note_kws = 'nota|Nota'
page_kws = 'página'
added = 'Añadid. el'
locs = 'posición|Pos\.'


def get_highlight_data(hl):
    md = {}
    cont = hl.splitlines()
    cont = [md for md in cont if md != '']

    ## Book
    book = re.match(r'(?P<title>.*)\((?P<author>.*)\)', cont[0])
    md['title'] = book.group('title').strip()
    md['author'] = book.group('author').strip()
    ### defines if it's a note or a highlight -- So far, it only retrieves those elemets
    if re.search(highl_kws, cont[1]):
        md['type'] = 'highlight'
    elif re.search(note_kws, cont[1]):
        md['type'] = 'note'
    else:
        return None

    ## Location or position in the ebook
    loc = re.match(r'.*(' + locs + r') (?P<location>[0-9,-]+).*', cont[1])
    md['location'] = loc.group('location')
    ## Page
    try:
        pag = re.match(r'.*(' + page_kws + ') (?P<page>[0-9,-]+) |$', cont[1])
        md['page'] = pag.group('page')
    except:
        md['page'] = ''

    ## Date
    dateS = re.match(
        r".*(" + added + ") (?P<timestamp>.*) (?P<hour>[0-9]+)(H|:)(?P<minutes>[0-9]+)(H|:)(?P<seconds>[0-9]+)('|.)(?P<id>.*)$",
        cont[1])
    date = f"{dateS.group('timestamp')} {dateS.group('hour')}:{dateS.group('minutes')}:{dateS.group('seconds')}"
    date = date + dateS.group('id') if dateS.group('id') in ['AM', 'PM'] else date
    md['date_time'] = dateparser.parse(date)
    ### Assigns the body of the highlight or note
    md['highlight'] = cont[-1]
    return md


def get_highlights(path=path_highlights, separator=separator, encoding="utf-8-sig"):
    csv = {}
    location = {}

    with open(path, encoding=encoding) as kindle_file:
        highlights_list = kindle_file.read().split(separator)

        for hl in highlights_list:
            if hl != '\n':
                md = get_highlight_data(hl)
                if md:
                    title = md['highlight'][:50]

                    if md['type'] == "highlight":
                        loc = md['location'].split('-')[-1]
                        location[loc] = md['date_time']
                        csv[md['date_time']] = {"title": title, "date": md['date_time'], "text": md['highlight'],
                                                "author": md['author'], "book": md['title'], "page": md['page'],
                                                "tags": ""}
                    elif md['type'] == "note":
                        dt = location[loc]
                        tag = md['highlight'].replace('.', ',')
                        if not tag[0].isalpha():
                            tag = tag[1:]

                        if dt in csv:
                            csv[dt]["tags"] = tag
                        else:
                            print(f"Cannot find this location {tag}.")

    return list(csv.values())


if __name__ == '__main__':
    print(get_highlights())
