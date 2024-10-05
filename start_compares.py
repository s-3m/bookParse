from mg.compare import main as mg_main
from moscow.just_compare import main as msk_main
import schedule



def main():
    mg_main()
    msk_main()


def super_main():
    schedule.every().day.at('03:00').do(main)

    while True:
        schedule.run_pending()


if __name__ == '__main__':
    super_main()