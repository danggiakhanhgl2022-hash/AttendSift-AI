"""Print an Argon2id administrator hash without echoing the raw password."""
from getpass import getpass
from argon2 import PasswordHasher, Type


def main():
    password = getpass('Admin password: ')
    if len(password) < 12:
        raise SystemExit('Use at least 12 characters.')
    confirm = getpass('Confirm password: ')
    if password != confirm:
        raise SystemExit('Passwords do not match.')
    print(PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4,
                         type=Type.ID).hash(password))


if __name__ == '__main__':
    main()
