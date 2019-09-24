#!/usr/bin/env python3

from os import listdir, makedirs, rename, linesep
from os.path import isdir, exists, split, normpath, join, splitext
from urllib.parse import quote
import sys
import re
import subprocess

CPPCON_YEAR = 2017

def shell_call(cmd):
    process = subprocess.Popen(cmd, shell=True)
    process.wait()
    if process.returncode:
        print("'{}' failed.".format(cmd))
        print("Exit code:", process.returncode)

        exit(process.returncode)


def add_index(readme, category):
    readme.write("\n## {}\n\n".format(category).encode())
    generate_index(readme, category)


def make_readme(readme):
    with open('_tools/readme_header.md', mode='rb') as readme_header:
        readme.writelines(readme_header.readlines())
    readme.write("# Index of Materials\n".encode())
    CATEGORIES = [
        "Keynotes",
        "Presentations",
        "Tutorials",
        "Demos",
        "Lightning Talks and Lunch Sessions",
        "Posters"
    ]
    for category in CATEGORIES:
        add_index(readme, category)


def generate_entry(readme, session_name, path):
    def get_author_from_filename(path):
        author_regex = re.compile(".* - (.*) - CppCon " + str(CPPCON_YEAR) +
                                    "\\.[^.]*$")

        author = author_regex.search(path)

        if author:
            return author.group(1)

        return ""

    def get_author_from_readme_md(path):
        readme_header_regex = re.compile(r"\*\*(.*)\*\* by \*\*(.*)\*\*")

        with open(path, mode='rb') as readme_md:
            header = readme_md.readline().decode()
            match = readme_header_regex.match(header)

            if match:
                return match.group(2)

        return ""

    def md_path(path):
        return quote(normpath(path).replace('\\', '/'))

    presentation_regex = re.compile("- CppCon " + str(CPPCON_YEAR) +
                                    "\\.[^.]*$")
    pdf_regex = re.compile("\\.pdf$", flags=re.I)
    readme_md_regex = re.compile("README\\.md$")

    readme_md_file = ""
    presentation_file = ""
    all_presentation_files = []
    all_other_files = []
    author = ""

    dir_contents = listdir(path)

    for name in dir_contents:
        if presentation_regex.search(name):
            # Pick the first file we found, but prefer a PDF file if there
            # is one
            if (not presentation_file) or pdf_regex.search(name):
                presentation_file = name
                author = get_author_from_filename(name)

            all_presentation_files.append(name)
        elif readme_md_regex.search(name):
            readme_md_file = name
        else:
            all_other_files.append(name)

    if all_presentation_files:
        presentation_path = join(path, presentation_file)
    else:
        presentation_path = path
        author = get_author_from_readme_md(join(path, readme_md_file))

    readme.write(" - [{}]({}) by {}".format(session_name,
                                     md_path(presentation_path),
                                     author).encode())

    if len(all_presentation_files) > 1:
        exts = [(splitext(f)[1].lower(), md_path(join(path, f))) for f in
                all_presentation_files]
        for e in exts:
            readme.write(" \\[[{}]({})\\]".format(e[0], e[1]).encode())

    if readme_md_file:
        readme.write(" \\[[README]({})\\]".format(
            md_path(join(path, readme_md_file))).encode())

    if all_other_files:
        readme.write(" \\[[more materials]({})\\]".format(md_path(path)))

    readme.write('\n'.encode())


def generate_index(readme, path):
    if not exists(path):
        print("Skipping", path, "since it doesn't exist yet")
        return

    dir_contents = listdir(path)
    dir_contents.sort(key=lambda s: s.lower())

    for name in dir_contents:
        try:
            # empty directories or other such issues get skipped over
            generate_entry(readme, name, join(path, name))
        except:
            pass


def add_presentation(path):
    session = ""
    while not session or session not in 'pktldo':
        session = input("[P]resentation, [K]eynote, [T]utorial, " +
                        "[L]ighting/Lunch, [D]emo, P[o]ster? ").lower()

    SESSION_MAP = {
        'p': ('Presentations', 'Presentation'),
        'k': ('Keynotes', 'Keynote'),
        't': ('Tutorials', 'Tutorial'),
        'l': ('Lightning Talks and Lunch Sessions',
              'Lightning Talk and Lunch Session'),
        'd': ('Demos', 'Demo'),
        'o': ('Posters', 'Poster')
    }
    folder = SESSION_MAP[session][0]
    session_type = SESSION_MAP[session][1]

    filename = split(path)[-1]
    ext = splitext(filename)[-1]
    title = ""
    author = ""

    if ext == '.md':
        readme_header_regex = re.compile(r"\*\*(.*)\*\* by \*\*(.*)\*\*")

        with open(filename, mode='rb') as readme:
            heading = readme.readline().decode()
            match = readme_header_regex.match(heading)

            if match:
                title = match.group(1)
                author = match.group(2)
    else:
        title_author_regex = re.compile("(.*) - (.*) - CppCon " +
                                        str(CPPCON_YEAR) + r"\.[^.]*$")

        title_author_match = title_author_regex.search(filename)
        if title_author_match:
            title = title_author_match.group(1)
            author = title_author_match.group(2)

        print("\nExtension is", ext)

    if not title or not author:
        title = input("Title: ")
        author = input("Author: ")

    ok = ''
    while ok != 'y':
        if ok != 'n':
            print("\n\nTitle:", title)
            print("Author:", author.encode().decode(sys.stdout.encoding,
                  errors='ignore'))
            ok = input('OK? [y/n]: ').lower()

        if ok == 'n':
            title = input("Title: ")
            author = input("Author: ")

        if filename != 'README.md':
            new_filename = "{} - {} - CppCon 2017{}".format(title, author,
                                                            ext)
        else:
            new_filename = filename
            contents = None
            with open(filename, mode='rb') as readme:
                contents = readme.readlines()
            contents[0] = '**{}** by **{}**'.format(title, author).encode()
            with open(filename, mode='wb') as readme:
                readme.writelines(contents)
        if any((c in "\\/:*?”<>|") for c in new_filename):
            print("Name or Author contains invalid characters.")
            ok = 'n'
        elif ok == 'n':
            ok = ''

    new_folder = join(folder, title)
    new_path = join(new_folder, new_filename)
    makedirs(new_folder, exist_ok=True)
    rename(path, new_path)
    shell_call('git add "{}"'.format(new_path))

    return title, author


if __name__ == '__main__':
    if not (exists('_tools') and isdir('_tools')):
        print("Run this from the CppCon2017 root.")
        exit(1)

    TITLE = None
    AUTHOR = None
    if len(sys.argv) == 2 and sys.argv[1]:
        TITLE, AUTHOR = add_presentation(sys.argv[1])

    with open('README.md', mode='wb') as readme:
        make_readme(readme)

    shell_call('git add README.md')
    if TITLE and AUTHOR:
        shell_call('git commit -v -m "Add {} by {}" -e'.format(TITLE, AUTHOR))
    else:
        shell_call('git commit -v -m "Updating index" -e')
