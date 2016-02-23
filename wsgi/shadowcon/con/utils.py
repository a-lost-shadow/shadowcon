def friendly_username(user):
    name = user.first_name + " " + user.last_name
    if "" == name.strip():
        name = user.username
    return name
