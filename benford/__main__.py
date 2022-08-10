#!/usr/bin/env python3

from .app import create_app


def main():
    create_app().run(host='0.0.0.0', port=8000, debug=True)


if __name__ == '__main__':
    main()
