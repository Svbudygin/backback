from bin_checker import get_bin

bin_information = get_bin('302596')  # example BIN
if bin_information.get('error', False):
    print(bin_information['bank_name'])  # you have a dict!