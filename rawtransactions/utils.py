from collections import defaultdict


def is_array_unique(array, key):
    uniques = defaultdict(lambda: True)
    for obj in array:
        value = uniques[obj[key]]
        if value:
            uniques[obj[key]] = None
        else:
            return False
    return True


def calculate_amount(lot_details):
    print(lot_details)
    amount = 0
    for detail in lot_details:
        amount += (
            detail["quantity"]
            * detail["rate"]
            * detail["actual_gazaana"]
            * (detail["formula"].numerator / detail["formula"].denominator)
        )
    return amount
