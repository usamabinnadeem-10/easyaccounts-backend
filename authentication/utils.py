import authentication.constants as constants


def validate_if_permissions_exist(permissions):
    all_permissions = []

    if hasattr(constants, "__all__"):
        all_permissions = [getattr(constants, name) for name in constants.__all__]
    else:
        all_permissions = [
            getattr(constants, name)
            for name in dir(constants)
            if not name.startswith("_")
        ]
    for perm in permissions:
        if not (perm in all_permissions):
            return False
    return True
