import random
import math


class AlgorithmCrash:
    e = 2 ** 52
    div = 33
    g = 2

    def check_g(self, g):
        g = round(g, 1)
        if g == 0:
            return 1
        return g

    def check_div(self, div):
        if div < 1:
            return 33
        return round(div, 2)

    def get_result(self):
        e = int(self.e)
        h = round(random.uniform(0, e - 1))
        g = self.check_g(self.g)
        div = self.check_div(self.div)
        if h % div == 0:
            return 1
        return round((0.99 * (pow(e / (e - h), 1 / g)) + 0.01), 2)


def calculate_flight_time(target_mult):
    x_value = 1000 * math.log(target_mult)
    frames = x_value / 1.6
    time_in_seconds = frames / 30
    return time_in_seconds