from ngap_rules import ngap_rules


def trouver_cotation(message):
    message = message.lower()

    for regle in ngap_rules:
        if all(keyword in message for keyword in regle["keywords"]):
            return regle

    return None
