#!/usr/bin/env python

import os
import sys

from .assembler import Assembler, AssemblyError
from .VM import VM

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

        self.commands = {
            '$RUN': 'Executa um arquivo',
            '$ASM': 'Monta um arquivo ASM',
            '$END': 'Encerra o interpretador',
            '$LOGOUT': 'Volta para o login',
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
                    self._end()
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

                    self._run(cmd[1])

                elif cmd[0] == '$LOGOUT':
                    self._logout()
                    print()
                    break

                elif cmd[0] == '$END':
                    self._end()

                elif cmd[0] == '$ASM':
                    if len(cmd) < 2:
                        print('Usage: $RUN <file>')
                        continue

                    self._asm(cmd[1])

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
            print(p.name)

    def _del(self):
        pass

    def _run(self, file):
        print('Running', file)

    def _asm(self, file):
        try:
            asm = Assembler(file)
            asm.assemble()
        except AssemblyError as e:
            print('Error:', e)

    def _end(self):
        print('bye!')
        sys.exit(0)
