def get_account_balances(final_account_balances, array, operation="add"):
    for value in array:
        current_amount = final_account_balances[value["account_type__name"]]
        if operation == "add":
            current_amount += value["total"]
        else:
            current_amount -= value["total"]
        final_account_balances[value["account_type__name"]] = current_amount
    return final_account_balances
