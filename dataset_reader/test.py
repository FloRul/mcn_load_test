import dataset_reader.utils as utils

def main():
    print(' reading files ')
    utils.readFiles('../datasets', True)
    print(' files read ')

if __name__ == "__main__":
    main()