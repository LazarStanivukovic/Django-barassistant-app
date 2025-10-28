# Aleksa Sekulic 0021/2022


from django.shortcuts import redirect


def redirect_by_role(user):
    """
    **Opis**

    Preusmerava prijavljenog korisnika na odgovarajuću stanu.

    :param: user: User
    :return: response: HTML
    """
    if user.zap.tip == 'K':
        nexturl = 'konobar'
    elif user.zap.tip == 'M':
        nexturl = 'menadzer'
    else:
        nexturl = 'admin'
    return redirect(nexturl)