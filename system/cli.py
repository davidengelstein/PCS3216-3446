#!/usr/bin/env python

import os
import sys

from .assembler import Assembler, AssemblyError
from .VM import VM, VMError

from passlib.hash import bcrypt
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

style = Style.from_dict({
    '':         '#ffffff',
    'username': '#0096FF',
    'path':     '#C0C0C0',
    'selected-text': 'reverse underline',
})

class Interpreter:
    def __init__(self):
        self.current_user = None
        self.current_dir = None

        self.base_path = os.getcwd()
        self.sys_path = 'system'
        self.user_path = 'users'

        self.vm = VM()

        self.commands = {
            '$RUN': 'Executa um arquivo OBJ',
            '$ASM': 'Monta um arquivo ASM',
            '$END': 'Encerra o interpretador',
            '$LOGOUT': 'Volta para o login',
            '$DEL': 'Marca um arquivo para remoção',
            '$DIR': 'Mostra os arquivos na pasta'
        }

    def start(self):
        while True:
            print('Welcome! (l)ogin or (r)egister')

            while self.current_user is None:
                cmd = prompt('login >> ').lower()

                if cmd in ['l', 'login']:
                    self.login()
                elif cmd in ['r', 'register']:
                    self.register()
                elif cmd == '$end':
                    self.end()
                else:
                    print('Command not found! (l)ogin or (r)egister')

            while True:
                prompt_fragments = [
                    ('class:username', self.current_user),
                    ('',  ' '),
                    ('class:path', self.current_dir),
                    ('', ' >> '),
                ]
                cmd = ''
                while len(cmd) == 0:
                    cmd = prompt(prompt_fragments, style=style).split()

                if cmd[0] not in self.commands:
                    self._usage()
                    continue

                if cmd[0] == '$DIR':
                    self._dir()

                elif cmd[0] == '$RUN':
                    if len(cmd) < 2:
                        print('Usage: $RUN <file>')
                        continue

                    self._run(cmd[1], len(cmd) >= 3 and cmd[2] == 'step')

                elif cmd[0] == '$LOGOUT':
                    self._logout()
                    print()
                    break

                elif cmd[0] == '$END':
                    self.end()

                elif cmd[0] == '$ASM':
                    if len(cmd) < 2:
                        print('Usage: $RUN <file>')
                        continue

                    self._asm(cmd[1])

                elif cmd[0] == '$DEL':
                    if len(cmd) < 2:
                        print('Usage: $DEL <file>')
                        continue

                    self._del(cmd[1])

                print()

    def _usage(self):
        print('Comando Inválido!')
        for k, v in self.commands.items():
            print('    {}: {}'.format(k, v))
        print()

    def login(self):
        user = prompt('User: ')

        with open(os.path.join(self.sys_path, 'passwd'), 'r') as f:
            lines = f.readlines()
            users  = [line.strip().split(':')[0] for line in lines]
            passes = [line.strip().split(':')[1] for line in lines]

        if user not in users:
            print('User not found')
            return False

        index = users.index(user)
        pass_hash = passes[index]

        if bcrypt.verify(prompt('Password: ', is_password=True), pass_hash):
            self.current_user = user
            self.current_dir = os.path.join(self.user_path, user)
            os.chdir(self.current_dir)
            return True

        print('Wrong Password')
        return False

    def _logout(self):
        self.current_user = None
        os.chdir(self.base_path)

    def register(self):
        user = prompt('User: ')

        with open(os.path.join(self.sys_path, 'passwd'), 'r') as f:
            lines = f.readlines()
            users  = [line.strip().split(':')[0] for line in lines]

        if user in users:
            print('User already registered!')
            return False

        pass_hash = bcrypt.hash(prompt('Password: ', is_password=True))

        with open(os.path.join(self.sys_path, 'passwd'), 'a') as f:
            f.write('{}:{}\n'.format(user, pass_hash))

        os.makedirs(os.path.join(self.user_path, user))

        return True

    def _dir(self):
        for p in os.scandir():
            if not p.name.endswith('.to_delete'):
                print(p.name)

    def _del(self, filen):
        found = False

        for f in os.scandir():
            if f.name == filen:
                os.rename(filen, filen + '.to_delete')
                found = True
                break

        if not found:
            print('Arquivo nao existe!')

    def _run(self, filen, step):
        try:
            self.vm.load(filen)
            self.vm.run(step)
        except VMError as e:
            print('Error:', e)

    def _asm(self, file):
        try:
            asm = Assembler(file)
            asm.assemble()
            print('Assembly terminado!')
        except AssemblyError as e:
            print('Error:', e)

    def end(self):
        print('Cleaning up!')
        for p in os.scandir():
            if p.name.endswith('.to_delete'):
                os.remove(p)
        print('Finished! Bye!')
        sys.exit(0)
