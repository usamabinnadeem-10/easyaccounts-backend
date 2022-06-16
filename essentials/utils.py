from cheques.choices import ChequeStatusChoices


def get_account_balances(final_account_balances, array, operation="add"):
    for value in array:
        current_amount = final_account_balances[value["account_type__name"]]
        if operation == "add":
            current_amount += value["total"]
        else:
            current_amount -= value["total"]
        final_account_balances[value["account_type__name"]] = current_amount
    return final_account_balances


def format_cheques_as_ledger(cheques, nature, serial_prefix):
    return list(
        map(
            lambda val: {
                **val,
                "nature": nature,
                "serial": f"{serial_prefix}-{val['serial']}",
            },
            cheques,
        )
    )


def add_type(array, serial_prefix):
    return list(
        map(
            lambda x: {**x, "serial": f"{serial_prefix}-{x['serial']}"},
            array,
        )
    )


def format_external_cheques_as_ledger(cheques, serial_prefix):
    return list(
        map(
            lambda x: {
                **x,
                "nature": "D" if x["status"] == ChequeStatusChoices.TRANSFERRED else "C",
                "serial": f"{serial_prefix}-{x['serial']}",
            },
            cheques,
        )
    )
