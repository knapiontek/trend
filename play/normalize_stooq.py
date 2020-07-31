import pathlib

import in_place


def run():
    source = '<TICKER>,<PER>,<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>,<OPENINT>'
    target = 'TICKER,PER,DATE,TIME,OPEN,HIGH,LOW,CLOSE,VOL,OPENINT'

    path = pathlib.Path('/home/kris/repos/trend/stooq/daily/uk/')
    for p in path.rglob('*.txt'):
        print(p)
        with in_place.InPlace(p) as fp:
            for line in fp:
                modified = line.replace(source, target)
                fp.write(modified)


def find_size():
    path = pathlib.Path('/home/kris/repos/trend/stooq/daily/uk/')
    for p in path.rglob('*.txt'):
        with open(str(p)) as fp:
            size = len(fp.readlines())
            if size > 1000:
                print(p, size)


if __name__ == '__main__':
    # run()
    find_size()
