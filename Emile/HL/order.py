from enum import Enum


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

class OrderCommand(Enum):
    Goto = 1


class Order:
    params: list
    command: OrderCommand

    def __init__(self, var: OrderCommand, params: list):
        self.params = params
        self.var = var

    def print(self):
        print(self.var.name)
        print(self.params)


def get_order():
    user_input = input().split()

    if len(user_input) == 0:
        return None

    order_type = []
    if user_input[0] == "goto":
        if len(user_input) != 3:
            return None
        for i in range(1, len(user_input)):
            if is_float(user_input[i]):
                order_type.append(float(user_input[i]))
        order = Order(OrderCommand.Goto, order_type)
        order.var = OrderCommand.Goto
        return order

    return None
