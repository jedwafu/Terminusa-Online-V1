from string import digits, ascii_lowercase, ascii_letters
import random

list1 = digits + ascii_lowercase
list2 = digits + ascii_letters


def generate_bank_card():
    return random.randint(10 ** 15, 10 ** 16)


def generate_eth():
    card = [random.choice(list1) for _ in range(42)]
    return ''.join(card)


def generate_usdt():
    card = [random.choice(list2) for _ in range(33)]
    return ''.join(card)


def generate_btc():
    card = [random.choice(list2) for _ in range(32)]
    return ''.join(card)
