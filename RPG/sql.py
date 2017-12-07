import sqlite3

class DB:
    def __init__(self, name: str):
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()

    def create(self):
        self.cur.execute('''CREATE TABLE characters
                       (id TEXT, img TEXT, width INT, height INT, num INT, st INT, x INT, y INT)''')
        self.conn.commit()

    def add(self):
        id = input('Введите ID: ').lower()
        img = input('Введите путь к изображению: ')
        width = 32
        height = 32
        num = 3
        st = 1
        n = int(input())
        y = (n // 4)*128
        x = (n % 4)*96
        self.cur.execute('''INSERT INTO characters (id, img, width, height, num, st, x, y) 
                            VALUES ('%s','%s', %i, %i, %i, %i, %i, %i)'''
                         % (id, img, width, height, num, st, x, y))

    def search(self, id: str) -> (str, int, int, int, int):
        id = id.lower()
        self.cur.execute("SELECT * FROM characters WHERE id LIKE '%s'" % (id,))
        out = self.cur.fetchone()
        return out[1:]

    def get(self):
        self.cur.execute("SELECT * FROM characters")
        row = self.cur.fetchone()
        while row is not None:
            print(row)
            row = self.cur.fetchone()

    def add_set(self):
        id = input('Введите ID: ').lower()
        img = input('Введите путь к изображению: ')
        width = 32
        height = 32
        num = 3
        st = 1
        for i in range(8):
            y = (i // 4) * 128
            x = (i % 4) * 96
            self.cur.execute('''INSERT INTO characters (id, img, width, height, num, st, x, y) 
                                        VALUES ('%s','%s', %i, %i, %i, %i, %i, %i)'''
                             % (id+str(i).zfill(2), img, width, height, num, st, x, y))


if __name__ == "__main__":
    com = ''
    db = DB('Characters.sqlite')
    while com != 'QUIT':
        db.get()
        com = input('Введите команду: ').upper()
        if com == 'ADD':
            db.add()
        if com == 'SEA':
            print('>', db.search(input()))
        if com == 'ADDSET':
            db.add_set()
        if com == 'COMMIT':
            db.conn.commit()